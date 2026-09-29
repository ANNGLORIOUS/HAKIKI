from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        REPORTER = "reporter", "Reporter"
        SELLER = "seller", "Seller"
        MODERATOR = "moderator", "Moderator"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=16, unique=True, null=True, blank=True)  # +2547XXXXXXXX
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.REPORTER)
    # Internal only. Rises when a user's reports hold up; falls when they are rejected as false.
    reputation = models.IntegerField(default=0)

    @property
    def is_verified_reporter(self) -> bool:
        return self.phone_verified and self.email_verified

    @property
    def is_moderator(self) -> bool:
        return self.role == self.Role.MODERATOR or self.is_staff


class OTP(models.Model):
    """One-time code for verifying a phone number or email. Only a keyed hash of the code is stored."""

    class Channel(models.TextChoices):
        PHONE = "phone", "Phone"
        EMAIL = "email", "Email"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    channel = models.CharField(max_length=6, choices=Channel.choices)
    target = models.CharField(max_length=255)  # normalized phone or email being verified
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
