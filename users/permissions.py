from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Only clinic staff can do that."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", "") == "admin")
