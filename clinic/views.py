from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdminRole

from .booking import confirmation_text
from .models import Appointment, AppointmentSlot, Doctor
from .serializers import (
    AppointmentSerializer,
    BookAppointmentSerializer,
    DoctorSerializer,
    SlotSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Doctor.objects.all().order_by("full_name")
        return Doctor.objects.filter(is_active=True).order_by("full_name")

    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()
        has_booking = Appointment.objects.filter(slot__doctor=doctor, status="booked").exists()
        if has_booking:
            return Response(
                {"detail": "Cancel this doctor's bookings before removing the profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        doctor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SlotViewSet(viewsets.ModelViewSet):
    serializer_class = SlotSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = AppointmentSlot.objects.select_related("doctor")
        if self.request.user.role != "admin":
            today = timezone.localdate()
            qs = qs.filter(doctor__is_active=True, date__gte=today)

        doctor = self.request.query_params.get("doctor")
        if doctor:
            qs = qs.filter(doctor_id=doctor)

        if self.request.query_params.get("available") == "true":
            qs = qs.filter(is_available=True)

        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(date=date)

        return qs.order_by("date", "start_time")

    def destroy(self, request, *args, **kwargs):
        slot = self.get_object()
        if Appointment.objects.filter(slot=slot, status="booked").exists():
            return Response(
                {"detail": "This time is booked. Cancel the appointment first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        qs = Appointment.objects.select_related("patient", "slot", "slot__doctor")
        if self.request.user.role != "admin":
            qs = qs.filter(patient=self.request.user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.order_by("slot__date", "slot__start_time")

    def create(self, request, *args, **kwargs):
        if request.user.role != "patient":
            return Response(
                {"detail": "Only patients can book an appointment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = serializer.validated_data["slot"]
        reason = serializer.validated_data.get("reason", "")

        try:
            with transaction.atomic():
                slot = AppointmentSlot.objects.select_related("doctor").get(pk=slot.pk)
                taken = Appointment.objects.filter(slot=slot, status="booked").exists()
                if (not slot.is_available) or taken:
                    return Response(
                        {"detail": "That time has just been booked. Please pick another slot."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not slot.doctor.is_active:
                    return Response(
                        {"detail": "This doctor is not taking bookings."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                appointment = Appointment.objects.create(
                    patient=request.user,
                    slot=slot,
                    reason=reason,
                    status="booked",
                    confirmation_message=confirmation_text(request.user, slot),
                )
                slot.is_available = False
                slot.save(update_fields=["is_available"])
        except IntegrityError:
            return Response(
                {"detail": "That time has just been booked. Please pick another slot."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        appointment = self.get_object()
        if request.user.role != "admin" and appointment.patient_id != request.user.id:
            return Response(
                {"detail": "You can only change your own appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status != "booked":
            return Response(
                {"detail": "This appointment is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = appointment.reason
        if "reason" in request.data:
            reason = request.data.get("reason") or ""

        try:
            new_slot_id = int(request.data.get("slot", appointment.slot_id))
        except (TypeError, ValueError):
            return Response({"detail": "Choose a valid time."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                appointment = Appointment.objects.select_related("patient", "slot", "slot__doctor").get(
                    pk=appointment.pk
                )
                if new_slot_id != appointment.slot_id:
                    try:
                        new_slot = AppointmentSlot.objects.select_related("doctor").get(pk=new_slot_id)
                    except AppointmentSlot.DoesNotExist:
                        return Response(
                            {"detail": "That slot does not exist."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    taken = Appointment.objects.filter(slot=new_slot, status="booked").exists()
                    if (not new_slot.is_available) or taken:
                        return Response(
                            {"detail": "That slot is no longer available."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    old_slot = appointment.slot
                    old_slot.is_available = True
                    old_slot.save(update_fields=["is_available"])
                    new_slot.is_available = False
                    new_slot.save(update_fields=["is_available"])
                    appointment.slot = new_slot

                appointment.reason = reason
                appointment.confirmation_message = confirmation_text(appointment.patient, appointment.slot)
                appointment.save()
        except IntegrityError:
            return Response(
                {"detail": "That slot is no longer available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.refresh_from_db()
        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if request.user.role != "admin" and appointment.patient_id != request.user.id:
            return Response(
                {"detail": "You can only cancel your own appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status == "cancelled":
            return Response(
                {"detail": "This appointment is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            appointment.status = "cancelled"
            appointment.confirmation_message = "This appointment has been cancelled."
            appointment.save()
            slot = appointment.slot
            slot.is_available = True
            slot.save(update_fields=["is_available"])

        return Response(AppointmentSerializer(appointment).data)
