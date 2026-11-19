from django.conf import settings
from django.db import models


class Doctor(models.Model):
    full_name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    room = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("doctor", "date", "start_time")

    def __str__(self):
        return f"{self.doctor} {self.date} {self.start_time}"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    slot = models.ForeignKey(AppointmentSlot, on_delete=models.CASCADE, related_name="appointments")
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    confirmation_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Stops two active bookings for the same time, even if two requests arrive together.
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=models.Q(status="booked"),
                name="only_one_active_booking_per_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient} - {self.slot} ({self.status})"
