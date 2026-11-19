from django.contrib import admin

from .models import Appointment, AppointmentSlot, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialty", "room", "is_active")


@admin.register(AppointmentSlot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("doctor", "date", "start_time", "end_time", "is_available")
    list_filter = ("date", "is_available")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "slot", "status", "reason")
    list_filter = ("status",)
