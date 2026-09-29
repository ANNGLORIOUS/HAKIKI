from django.conf import settings
from django.db import models

from apps.listings.models import Page, PaymentIdentifier


class Report(models.Model):
    """An allegation by a user. Not a verdict."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        SCREENING = "screening", "Automated screening"
        UNDER_REVIEW = "under_review", "Under review"
        PUBLISHED = "published", "Published"
        DISPUTED = "disputed", "Disputed"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    class Category(models.TextChoices):
        NON_DELIVERY = "non_delivery", "Paid, never delivered"
        FAKE_ITEM = "fake_item", "Fake or counterfeit item"
        DEPOSIT_BLOCKED = "deposit_blocked", "Paid a deposit, then blocked"
        WRONG_ITEM = "wrong_item", "Wrong or very different item"
        STOLEN_VIDEO = "stolen_video", "Uses someone else's videos"
        IMPERSONATION = "impersonation", "Impersonating another business"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reports")
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="reports")
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField(max_length=3000)
    amount_kes = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    incident_date = models.DateField(null=True, blank=True)
    payment_identifier = models.ForeignKey(PaymentIdentifier, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports")
    whatsapp_identifier = models.ForeignKey(PaymentIdentifier, null=True, blank=True, on_delete=models.SET_NULL, related_name="whatsapp_reports")
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    duplicate_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="duplicates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.pk} on {self.page}"


def evidence_path(instance, filename):
    return f"evidence/{instance.report_id}/{filename}"


def vouch_path(instance, filename):
    return f"vouches/{instance.page_id}/{instance.user_id}/{filename}"


class Evidence(models.Model):
    """Supports a report. Its status is separate from the report's status."""

    class Status(models.TextChoices):
        NOT_REVIEWED = "not_reviewed", "Not reviewed"
        SUPPORTED = "supported", "Supported"
        INSUFFICIENT = "insufficient", "Insufficient"
        CONTRADICTED = "contradicted", "Contradicted"
        REDACTED = "redacted", "Redacted"

    class Kind(models.TextChoices):
        MPESA_MESSAGE = "mpesa_message", "M-Pesa message"
        CHAT_SCREENSHOT = "chat_screenshot", "Chat screenshot"
        PAGE_SCREENSHOT = "page_screenshot", "Page screenshot"
        VIDEO = "video", "Video"
        OTHER = "other", "Other"

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="evidence")
    file = models.FileField(upload_to=evidence_path)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.NOT_REVIEWED)
    moderator_note = models.CharField(max_length=255, blank=True)  # internal only
    created_at = models.DateTimeField(auto_now_add=True)


class Vouch(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vouches")
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="vouches")
    comment = models.TextField(max_length=1000, blank=True)
    proof = models.FileField(upload_to=vouch_path)  # M-Pesa message or delivery photo
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "page"], name="one_vouch_per_user_page")]


class CheckRequest(models.Model):
    """'Is this page legit?' from someone who hasn't bought. An opinion, never evidence."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="check_requests")
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CopyrightComplaint(models.Model):
    """Separate from scam reports: 'this account uses my video without permission'."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        UPHELD = "upheld", "Upheld"
        DISMISSED = "dismissed", "Dismissed"

    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="copyright_complaints")
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="copyright_complaints")
    original_url = models.URLField(max_length=500)
    infringing_url = models.URLField(max_length=500)
    description = models.TextField(max_length=2000)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
