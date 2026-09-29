import hmac
import secrets
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone

from apps.core.sms import send_sms
from apps.core.utils import hmac_hash

from .models import OTP

OTP_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def _digest(user_id, channel, code):
    return hmac_hash("otp:%s:%s:%s" % (user_id, channel, code))


def create_otp(user, channel, target):
    """Invalidate older codes, store a hash of a new 6-digit code, and return the code."""
    OTP.objects.filter(user=user, channel=channel, used=False).update(used=True)
    code = "%06d" % secrets.randbelow(10 ** 6)
    OTP.objects.create(
        user=user, channel=channel, target=target,
        code_hash=_digest(user.pk, channel, code),
        expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
    )
    return code


def deliver(channel, target, code):
    if channel == OTP.Channel.PHONE:
        send_sms(target, "Your Hakiki verification code is %s. It expires in %d minutes." % (code, OTP_TTL_MINUTES))
    else:
        send_mail(
            "Your Hakiki verification code",
            "Your verification code is %s. It expires in %d minutes.\n\nIf you didn't request this, ignore this email." % (code, OTP_TTL_MINUTES),
            None, [target],
        )


def check_otp(user, channel, code):
    """Return the OTP row if the code is right, else None. Limits guesses to 5 per code."""
    otp = OTP.objects.filter(user=user, channel=channel, used=False).order_by("-created_at").first()
    if not otp or otp.expires_at < timezone.now() or otp.attempts >= MAX_ATTEMPTS:
        return None
    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if not hmac.compare_digest(otp.code_hash, _digest(user.pk, channel, str(code).strip())):
        return None
    otp.used = True
    otp.save(update_fields=["used"])
    return otp
