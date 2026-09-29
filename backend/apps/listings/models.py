from django.conf import settings
from django.db import models

from apps.core.utils import decrypt, encrypt, hmac_hash, mask_value, normalize_payment_value


class Platform(models.TextChoices):
    TIKTOK = "tiktok", "TikTok"
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"
    WHATSAPP = "whatsapp", "WhatsApp"
    OTHER = "other", "Other"


class Page(models.Model):
    """A seller's social page. One row per (platform, handle)."""

    class Label(models.TextChoices):
        NO_REPORTS = "no_reports", "No reports yet"
        NEEDS_CHECKING = "needs_checking", "Needs checking"
        REPORTS_REVIEW = "reports_review", "Reports received, review ongoing"
        REPORTED_MULTIPLE = "reported_multiple", "Reported by multiple users"
        VOUCHED = "vouched", "Vouched by buyers"
        MIXED = "mixed", "Mixed"
        DISPUTED = "disputed", "Disputed"
        RESOLVED = "resolved", "Resolved"

    platform = models.CharField(max_length=12, choices=Platform.choices)
    handle = models.CharField(max_length=60)  # normalized, lowercase, no '@'
    display_name = models.CharField(max_length=120, blank=True)
    public_label = models.CharField(max_length=20, choices=Label.choices, default=Label.NO_REPORTS)
    label_updated_at = models.DateTimeField(auto_now_add=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    # Set once a seller proves ownership (code in bio)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_pages")
    verified_owner = models.BooleanField(default=False)
    claim_code = models.CharField(max_length=16, blank=True)
    # Only pages that pass moderation and the report threshold are indexed by Google
    indexable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["platform", "handle"], name="uniq_platform_handle")]
        indexes = [models.Index(fields=["handle"])]

    def __str__(self):
        return f"{self.platform}:@{self.handle}"

    @property
    def profile_url(self):
        base = {"tiktok": "https://www.tiktok.com/@", "instagram": "https://www.instagram.com/", "facebook": "https://www.facebook.com/"}
        return base.get(self.platform, "") + self.handle if self.platform in base else ""


class PageLabelHistory(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="label_history")
    label = models.CharField(max_length=20, choices=Page.Label.choices)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PaymentIdentifier(models.Model):
    """A phone number, Till, Paybill or bank account seen in reports.

    Stored encrypted for admins; matched via HMAC hash; shown publicly only as a masked value
    and a count. Never expose `value` or `hash` through the public API.
    """

    class IdType(models.TextChoices):
        SEND_MONEY = "send_money", "M-Pesa Send Money (phone)"
        TILL = "till", "Till number"
        PAYBILL = "paybill", "Paybill"
        BANK = "bank", "Bank account"
        WHATSAPP = "whatsapp", "WhatsApp number"

    id_type = models.CharField(max_length=12, choices=IdType.choices)
    value_encrypted = models.TextField()
    value_hash = models.CharField(max_length=64, db_index=True)
    masked = models.CharField(max_length=32)
    registered_name = models.CharField(max_length=120, blank=True)  # name M-Pesa showed the payer
    first_seen = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["id_type", "value_hash"], name="uniq_idtype_hash")]

    def __str__(self):
        return f"{self.id_type} {self.masked}"

    @classmethod
    def hash_for(cls, id_type: str, raw: str) -> str:
        normalized = normalize_payment_value("send_money" if id_type == "whatsapp" else id_type, raw)
        return hmac_hash(f"{id_type}:{normalized}")

    @classmethod
    def get_or_create_from_raw(cls, id_type: str, raw: str, registered_name: str = ""):
        normalized = normalize_payment_value("send_money" if id_type == "whatsapp" else id_type, raw)
        h = hmac_hash(f"{id_type}:{normalized}")
        obj, created = cls.objects.get_or_create(
            id_type=id_type,
            value_hash=h,
            defaults={"value_encrypted": encrypt(normalized), "masked": mask_value(normalized), "registered_name": registered_name},
        )
        if not created and registered_name and not obj.registered_name:
            obj.registered_name = registered_name
            obj.save(update_fields=["registered_name"])
        return obj, created

    def reveal(self) -> str:
        """Admin/moderator use only. Callers must write a ModerationAction when revealing."""
        return decrypt(self.value_encrypted)


class PagePayment(models.Model):
    """Links a page to a payment identifier. Two pages sharing one identifier are 'potentially related'."""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="payments")
    identifier = models.ForeignKey(PaymentIdentifier, on_delete=models.CASCADE, related_name="page_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page", "identifier"], name="uniq_page_identifier")]


class OwnershipClaim(models.Model):
    """A seller asking to be recognised as the owner of a page by placing a code in their bio."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="claims")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="claims")
    code = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page", "user"], name="one_claim_per_user_page")]
