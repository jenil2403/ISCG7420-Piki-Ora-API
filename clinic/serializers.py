from rest_framework import serializers

from .models import Appointment, AppointmentSlot, Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ["id", "full_name", "specialty", "email", "phone", "room", "bio", "is_active"]


class SlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    specialty = serializers.CharField(source="doctor.specialty", read_only=True)

    class Meta:
        model = AppointmentSlot
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "specialty",
            "date",
            "start_time",
            "end_time",
            "is_available",
        ]

    def validate(self, data):
        start = data.get("start_time") or getattr(self.instance, "start_time", None)
        end = data.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and end <= start:
            raise serializers.ValidationError("End time must be after the start time.")
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor = serializers.IntegerField(source="slot.doctor_id", read_only=True)
    doctor_name = serializers.CharField(source="slot.doctor.full_name", read_only=True)
    date = serializers.DateField(source="slot.date", read_only=True)
    start_time = serializers.TimeField(source="slot.start_time", read_only=True)
    end_time = serializers.TimeField(source="slot.end_time", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "slot",
            "doctor",
            "doctor_name",
            "date",
            "start_time",
            "end_time",
            "reason",
            "status",
            "confirmation_message",
            "created_at",
        ]
        read_only_fields = ["patient", "status", "confirmation_message", "created_at"]

    def get_patient_name(self, obj):
        full = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return full or obj.patient.username


class BookAppointmentSerializer(serializers.Serializer):
    slot = serializers.PrimaryKeyRelatedField(queryset=AppointmentSlot.objects.all())
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
