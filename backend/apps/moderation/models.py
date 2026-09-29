from django.conf import settings
from django.db import models

from apps.submissions.models import Report


class ModerationAction(models.Model):
    """Append-only audit log. Rows can never be edited or deleted."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="moderation_actions")
    action = models.CharField(max_length=60)  # e.g. report.published, evidence.redacted, identifier.revealed
    target_type = models.CharField(max_length=40)
    target_id = models.PositiveBigIntegerField()
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Audit log entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit log entries cannot be deleted.")

    @classmethod
    def log(cls, actor, action, target, before=None, after=None, reason=""):
        return cls.objects.create(
            actor=actor, action=action, target_type=target.__class__.__name__.lower(),
            target_id=target.pk, before=before, after=after, reason=reason,
        )


class Dispute(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNDER_REVIEW = "under_review", "Under review"
        DECIDED = "decided", "Decided"

    class Decision(models.TextChoices):
        REMAINS = "remains", "Report stays"
        MODIFIED = "modified", "Report modified"
        REMOVED = "removed", "Report removed"

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="disputes")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="disputes")
    statement = models.TextField(max_length=3000)
    proof = models.FileField(upload_to="disputes/", blank=True)
    status = models.CharField(max_length=14, choices=Status.choices, default=Status.OPEN)
    decision = models.CharField(max_length=10, choices=Decision.choices, blank=True)
    decision_note = models.TextField(blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)


class Appeal(models.Model):
    """One appeal per dispute, reviewed by a different moderator than the original decision."""

    dispute = models.OneToOneField(Dispute, on_delete=models.CASCADE, related_name="appeal")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    statement = models.TextField(max_length=3000)
    outcome = models.CharField(max_length=10, choices=Dispute.Decision.choices, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
