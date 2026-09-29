from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.utils import mask_value, normalize_msisdn

from .models import User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        try:
            return normalize_msisdn(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class CodeSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


def user_payload(user):
    return {
        "id": user.pk,
        "email": user.email,
        "phone": mask_value(user.phone) if user.phone else None,
        "phone_verified": user.phone_verified,
        "email_verified": user.email_verified,
        "is_verified_reporter": user.is_verified_reporter,
        "role": user.role,
    }
