from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from clinic.booking import confirmation_text
from clinic.models import Appointment, AppointmentSlot, Doctor
from users.models import User


class Command(BaseCommand):
    help = "Create the demo admin, a sample patient, doctors and open times."

    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(username="admin")
        admin_user.email = "admin@pikiora.example"
        admin_user.first_name = "Moana"
        admin_user.last_name = "Clarke"
        admin_user.role = "admin"
        admin_user.phone = "09 555 0100"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password("Admin12345")
        admin_user.save()

        patient, made_patient = User.objects.get_or_create(
            username="avery",
            defaults={
                "email": "avery.singh@email.example",
                "first_name": "Avery",
                "last_name": "Singh",
                "role": "patient",
                "phone": "021 555 0133",
            },
        )
        if made_patient:
            patient.set_password("Patient12345")
            patient.save()

        if Doctor.objects.exists():
            self.stdout.write(self.style.SUCCESS("Sample doctors already exist. Admin login was refreshed."))
            self.stdout.write("Admin username: admin  password: Admin12345")
            return

        doctor_rows = [
            {
                "full_name": "Hana Bennett",
                "specialty": "General Practitioner",
                "email": "hana.bennett@pikiora.example",
                "phone": "09 555 0142",
                "room": "Room 1",
                "bio": "Everyday appointments, repeat prescriptions and check-ups.",
            },
            {
                "full_name": "Joseph Malik",
                "specialty": "General Practitioner",
                "email": "joseph.malik@pikiora.example",
                "phone": "09 555 0168",
                "room": "Room 2",
                "bio": "Sees adults for new problems and follow-up visits.",
            },
            {
                "full_name": "Sione Tafiti",
                "specialty": "Child health",
                "email": "sione.tafiti@pikiora.example",
                "phone": "09 555 0175",
                "room": "Room 3",
                "bio": "Appointments for children and youth.",
            },
        ]
        doctors = [Doctor.objects.create(**row) for row in doctor_rows]

        days = []
        next_day = timezone.localdate() + timedelta(days=1)
        while len(days) < 3:
            if next_day.weekday() < 5:
                days.append(next_day)
            next_day += timedelta(days=1)

        hours = [
            (time(9, 0), time(9, 20)),
            (time(11, 0), time(11, 20)),
            (time(14, 0), time(14, 20)),
        ]

        first_slot = None
        for doctor in doctors:
            for day in days:
                for start, end in hours:
                    slot = AppointmentSlot.objects.create(
                        doctor=doctor,
                        date=day,
                        start_time=start,
                        end_time=end,
                    )
                    if first_slot is None and doctor == doctors[0]:
                        first_slot = slot

        first_slot.is_available = False
        first_slot.save(update_fields=["is_available"])
        Appointment.objects.create(
            patient=patient,
            slot=first_slot,
            reason="Sore throat",
            status="booked",
            confirmation_message=confirmation_text(patient, first_slot),
        )

        self.stdout.write(self.style.SUCCESS("Sample data created."))
        self.stdout.write("Admin username: admin  password: Admin12345")
        self.stdout.write("Patient username: avery  password: Patient12345")
