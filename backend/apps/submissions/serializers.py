from datetime import date
from decimal import Decimal

from rest_framework import serializers

from apps.core.utils import parse_social
from apps.listings.models import PaymentIdentifier, Platform

from .models import Evidence, Report


class PageRefMixin(serializers.Serializer):
    """Accepts a platform plus a handle or profile link and resolves it to one normalized handle."""

    platform = serializers.ChoiceField(choices=Platform.choices)
    handle = serializers.CharField(max_length=300, help_text="@handle or profile link")

    def validate(self, attrs):
        try:
            attrs["handle"] = parse_social(attrs["platform"], attrs["handle"])
        except ValueError as e:
            raise serializers.ValidationError({"handle": str(e)})
        return attrs


class ReportCreateSerializer(PageRefMixin):
    category = serializers.ChoiceField(choices=Report.Category.choices)
    description = serializers.CharField(min_length=20, max_length=3000)
    amount_kes = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))
    incident_date = serializers.DateField(required=False, allow_null=True)
    payment_type = serializers.ChoiceField(choices=[c for c in PaymentIdentifier.IdType.choices if c[0] != "whatsapp"], required=False)
    payment_value = serializers.CharField(max_length=30, required=False, allow_blank=True)
    registered_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_incident_date(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("The date can't be in the future.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        from apps.core.utils import normalize_msisdn, normalize_payment_value

        pv, pt = attrs.get("payment_value", ""), attrs.get("payment_type")
        if bool(pv) != bool(pt):
            raise serializers.ValidationError({"payment_value": "Choose the payment type and enter the number."})
        if pv:
            try:
                normalize_payment_value(pt, pv)
            except ValueError as e:
                raise serializers.ValidationError({"payment_value": str(e)})
        wa = attrs.get("whatsapp_number", "")
        if wa:
            try:
                normalize_msisdn(wa)
            except ValueError as e:
                raise serializers.ValidationError({"whatsapp_number": str(e)})
        return attrs


class VouchCreateSerializer(PageRefMixin):
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class CheckRequestSerializer(PageRefMixin):
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class CopyrightComplaintSerializer(PageRefMixin):
    original_url = serializers.URLField(max_length=500)
    infringing_url = serializers.URLField(max_length=500)
    description = serializers.CharField(min_length=20, max_length=2000)


REPORTER_STATUS_TEXT = {
    "submitted": "Received",
    "screening": "Being screened",
    "under_review": "Under review by a moderator",
    "published": "Published",
    "disputed": "Published, disputed by the seller",
    "resolved": "Resolved",
    "rejected": "Not published",
}


def my_report_payload(r):
    return {
        "id": r.pk,
        "platform": r.page.platform,
        "handle": r.page.handle,
        "category": r.category,
        "status": r.status,
        "status_text": REPORTER_STATUS_TEXT[r.status],
        "evidence_count": r.evidence.count(),
        "created_at": r.created_at,
    }
