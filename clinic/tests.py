from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from clinic.models import AppointmentSlot, Doctor
from users.models import User


class ClinicApiTests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient1",
            password="Patient12345",
            role="patient",
            first_name="Pat",
        )
        self.admin = User.objects.create_user(
            username="staff1",
            password="Admin12345",
            role="admin",
        )
        self.doctor = Doctor.objects.create(
            full_name="Hana Bennett",
            specialty="General Practitioner",
            email="hana@pikiora.example",
        )
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date="2026-12-01",
            start_time="09:00",
            end_time="09:20",
        )
        self.other_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date="2026-12-01",
            start_time="10:30",
            end_time="10:50",
        )

    def login(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_health_is_public(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)

    def test_doctors_need_login(self):
        response = self.client.get("/api/doctors/")
        self.assertEqual(response.status_code, 401)

    def test_register_creates_a_patient(self):
        response = self.client.post(
            "/api/register/",
            {
                "username": "sam",
                "email": "sam@email.example",
                "password": "Patient12345",
                "first_name": "Sam",
                "last_name": "Lee",
                "role": "admin",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["role"], "patient")

    def test_patient_cannot_add_a_doctor(self):
        self.login(self.patient)
        response = self.client.post(
            "/api/doctors/",
            {
                "full_name": "New Doctor",
                "specialty": "GP",
                "email": "new@pikiora.example",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_add_a_doctor(self):
        self.login(self.admin)
        response = self.client.post(
            "/api/doctors/",
            {
                "full_name": "New Doctor",
                "specialty": "GP",
                "email": "new@pikiora.example",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_double_booking_is_rejected(self):
        self.login(self.patient)
        first = self.client.post(
            "/api/appointments/",
            {"slot": self.slot.id, "reason": "Check up"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertIn("Confirmed", first.data["confirmation_message"])

        second = self.client.post(
            "/api/appointments/",
            {"slot": self.slot.id, "reason": "Again"},
            format="json",
        )
        self.assertEqual(second.status_code, 400)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_available)

    def test_cancel_frees_the_slot(self):
        self.login(self.patient)
        booked = self.client.post(
            "/api/appointments/",
            {"slot": self.slot.id, "reason": "Check up"},
            format="json",
        )
        cancel = self.client.post(f"/api/appointments/{booked.data['id']}/cancel/")
        self.assertEqual(cancel.status_code, 200)

        other = User.objects.create_user(username="other", password="Patient12345", role="patient")
        self.login(other)
        again = self.client.post(
            "/api/appointments/",
            {"slot": self.slot.id, "reason": "Follow up"},
            format="json",
        )
        self.assertEqual(again.status_code, 201)

    def test_patient_only_sees_own_appointments(self):
        self.login(self.patient)
        self.client.post("/api/appointments/", {"slot": self.slot.id, "reason": "Mine"}, format="json")

        other = User.objects.create_user(username="other", password="Patient12345", role="patient", first_name="Olly")
        self.login(other)
        self.client.post("/api/appointments/", {"slot": self.other_slot.id, "reason": "Theirs"}, format="json")

        listing = self.client.get("/api/appointments/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(listing.data[0]["reason"], "Theirs")
