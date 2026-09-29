from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsModerator, IsVerifiedReporter
from apps.core.uploads import process_upload
from apps.listings.services import refresh_label
from apps.submissions.models import Report

from .models import Appeal, Dispute, ModerationAction

Decision = Dispute.Decision


class StatementSerializer(serializers.Serializer):
    statement = serializers.CharField(min_length=20, max_length=3000)


class DecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=Decision.choices)
    note = serializers.CharField(min_length=10, max_length=2000)


def apply_decision(report, decision, actor, reason):
    """Removed reports become 'resolved' (hidden from counts). Otherwise the report goes back to published."""
    before = {"status": report.status}
    report.status = Report.Status.RESOLVED if decision == Decision.REMOVED else Report.Status.PUBLISHED
    report.save(update_fields=["status", "updated_at"])
    ModerationAction.log(actor, "report.%s" % decision, report, before, {"status": report.status}, reason)
    page = report.page
    page.last_reviewed_at = timezone.now()
    page.save(update_fields=["last_reviewed_at"])
    refresh_label(page, actor, "Dispute decision: %s" % decision)


class DisputeCreateView(APIView):
    """The verified owner of a page disputes a published report about it."""

    permission_classes = [IsVerifiedReporter]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, report_id):
        report = get_object_or_404(Report.objects.select_related("page"), pk=report_id, status=Report.Status.PUBLISHED)
        page = report.page
        if not (page.verified_owner and page.owner_id == request.user.pk):
            raise PermissionDenied("Only the verified owner of this page can dispute its reports.")
        s = StatementSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        proof = request.FILES.get("proof")
        content = process_upload(proof, allow_video=False)[0] if proof else None
        with transaction.atomic():
            dispute = Dispute.objects.create(report=report, seller=request.user, statement=s.validated_data["statement"])
            if content:
                dispute.proof = content
                dispute.save(update_fields=["proof"])
            report.status = Report.Status.DISPUTED
            report.save(update_fields=["status", "updated_at"])
            ModerationAction.log(request.user, "dispute.opened", report, {"status": "published"}, {"status": "disputed"}, dispute.statement[:200])
            refresh_label(page, request.user, "Dispute opened")
        return Response({"id": dispute.pk, "message": "Dispute received. The report stays visible while we review it."}, status=201)


class AppealCreateView(APIView):
    """One appeal per dispute, by the seller, after a decision that kept the report."""

    permission_classes = [IsVerifiedReporter]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(Dispute.objects.select_related("report__page"), pk=dispute_id, seller=request.user)
        if dispute.status != Dispute.Status.DECIDED or dispute.decision == Decision.REMOVED:
            raise ValidationError({"detail": "This dispute can't be appealed."})
        if hasattr(dispute, "appeal"):
            raise ValidationError({"detail": "You've already appealed this decision."})
        s = StatementSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        appeal = Appeal.objects.create(dispute=dispute, submitted_by=request.user, statement=s.validated_data["statement"])
        ModerationAction.log(request.user, "appeal.opened", dispute, reason=appeal.statement[:200])
        return Response({"id": appeal.pk, "message": "Appeal received. A different moderator will review it."}, status=201)


class DisputeDecideView(APIView):
    permission_classes = [IsModerator]

    def post(self, request, dispute_id):
        dispute = get_object_or_404(
            Dispute.objects.select_related("report__page"), pk=dispute_id,
            status__in=[Dispute.Status.OPEN, Dispute.Status.UNDER_REVIEW],
        )
        s = DecisionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            dispute.status = Dispute.Status.DECIDED
            dispute.decision = d["decision"]
            dispute.decision_note = d["note"]
            dispute.decided_by = request.user
            dispute.decided_at = timezone.now()
            dispute.save()
            apply_decision(dispute.report, d["decision"], request.user, d["note"])
        return Response({"status": "decided", "decision": d["decision"]})


class AppealDecideView(APIView):
    permission_classes = [IsModerator]

    def post(self, request, appeal_id):
        appeal = get_object_or_404(Appeal.objects.select_related("dispute__report__page"), pk=appeal_id, outcome="")
        if appeal.dispute.decided_by_id == request.user.pk:
            raise PermissionDenied("An appeal must be reviewed by a different moderator than the original decision.")
        s = DecisionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            appeal.outcome = d["decision"]
            appeal.reviewed_by = request.user
            appeal.decided_at = timezone.now()
            appeal.save()
            apply_decision(appeal.dispute.report, d["decision"], request.user, d["note"])
        return Response({"status": "decided", "outcome": d["decision"]})
