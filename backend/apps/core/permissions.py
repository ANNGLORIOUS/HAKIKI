from rest_framework.permissions import BasePermission


class IsVerifiedReporter(BasePermission):
    message = "Please verify your phone number and email before submitting."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_verified_reporter)


class IsModerator(BasePermission):
    message = "Moderator access only."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_moderator)
