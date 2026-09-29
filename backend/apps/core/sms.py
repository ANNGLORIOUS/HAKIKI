import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(to, message):
    """Send an SMS. 'console' prints it (development). 'africastalking' sends it for real."""
    if getattr(settings, "SMS_BACKEND", "console") == "africastalking":
        return _send_africastalking(to, message)
    print("\n[SMS to %s] %s\n" % (to, message))
    logger.info("SMS (console) to %s", to)


def _send_africastalking(to, message):
    # NOTE: written from Africa's Talking's public API docs; test it with your sandbox account first.
    import requests

    sandbox = settings.AT_USERNAME == "sandbox"
    url = "https://api.%safricastalking.com/version1/messaging" % ("sandbox." if sandbox else "")
    data = {"username": settings.AT_USERNAME, "to": to, "message": message}
    if settings.AT_SENDER_ID:
        data["from"] = settings.AT_SENDER_ID
    resp = requests.post(
        url,
        data=data,
        headers={"apiKey": settings.AT_API_KEY, "Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
