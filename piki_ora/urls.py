from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from clinic.views import AppointmentViewSet, DoctorViewSet, SlotViewSet, health
from users.views import LoginView, LogoutView, MeView, PatientViewSet, RegisterView

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("slots", SlotViewSet, basename="slot")
router.register("appointments", AppointmentViewSet, basename="appointment")
router.register("patients", PatientViewSet, basename="patient")

urlpatterns = [
    # The staff screens for marking are in the React app.
    # This Django admin page is only a backup view of the tables.
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/register/", RegisterView.as_view()),
    path("api/login/", LoginView.as_view()),
    path("api/logout/", LogoutView.as_view()),
    path("api/me/", MeView.as_view()),
    path("api/", include(router.urls)),
]
