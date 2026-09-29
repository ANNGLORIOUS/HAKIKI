from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsVerifiedReporter
from apps.core.uploads import MAX_FILES, process_upload
from apps.listings.models import Page, PagePayment, PaymentIdentifier
from apps.listings.services import refresh_label

from .models import CheckRequest, CopyrightComplaint, Evidence, Report, Vouch
from .serializers import (
    CheckRequestSerializer, CopyrightComplaintSerializer, ReportCreateSerializer,
    VouchCreateSerializer, my_report_payload,
)
from .tasks import screen_report

MAX_REPORTS_PER_DAY = 5


class ReportCreateView(APIView):
    permission_classes = [IsVerifiedReporter]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        s = ReportCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = request.user

        if Report.objects.filter(reporter=user, created_at__gte=timezone.now() - timedelta(days=1)).count() >= MAX_REPORTS_PER_DAY:
            raise Throttled(detail="You've reached today's report limit. Please try again tomorrow.")

        files = request.FILES.getlist("files")
        if not files:
            raise ValidationError({"files": "Attach at least one screenshot, such as your M-Pesa message or the chat."})
        if len(files) > MAX_FILES:
            raise ValidationError({"files": "You can attach up to %d files." % MAX_FILES})
        kinds = request.data.getlist("kinds") if hasattr(request.data, "getlist") else []
        valid_kinds = {c[0] for c in Evidence.Kind.choices}
        processed = []
        for i, f in enumerate(files):
            content, _ = process_upload(f)  # validates before anything is saved
            kind = kinds[i] if i < len(kinds) and kinds[i] in valid_kinds else "other"
            processed.append((content, kind))

        with transaction.atomic():
            page, _ = Page.objects.get_or_create(platform=d["platform"], handle=d["handle"])
            if Report.objects.filter(reporter=user, page=page).exclude(status=Report.Status.REJECTED).exists():
                raise ValidationError({"detail": "You've already reported this page. You can follow it under My reports."})

            payment = whatsapp = None
            if d.get("payment_value"):
                payment, _ = PaymentIdentifier.get_or_create_from_raw(d["payment_type"], d["payment_value"], d.get("registered_name", ""))
                PagePayment.objects.get_or_create(page=page, identifier=payment)
            if d.get("whatsapp_number"):
                whatsapp, _ = PaymentIdentifier.get_or_create_from_raw("whatsapp", d["whatsapp_number"])
                PagePayment.objects.get_or_create(page=page, identifier=whatsapp)

            report = Report.objects.create(
                reporter=user, page=page, category=d["category"], description=d["description"],
                amount_kes=d.get("amount_kes"), incident_date=d.get("incident_date"),
                payment_identifier=payment, whatsapp_identifier=whatsapp,
            )
            for content, kind in processed:
                Evidence.objects.create(report=report, file=content, kind=kind)

        screen_report.delay(report.pk)
        refresh_label(page, reason="Report received")
        return Response(
            {"id": report.pk, "status": "submitted",
             "message": "Thank you. A moderator will review your report. Reports are only published once evidence is reviewed."},
            status=status.HTTP_201_CREATED,
        )


class MyReportsView(APIView):
    def get(self, request):
        qs = Report.objects.filter(reporter=request.user).select_related("page")
        return Response([my_report_payload(r) for r in qs])


class VouchCreateView(APIView):
    permission_classes = [IsVerifiedReporter]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        s = VouchCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        proof = request.FILES.get("proof")
        if not proof:
            raise ValidationError({"proof": "Attach proof of your purchase, such as your M-Pesa message or a delivery photo."})
        content, _ = process_upload(proof, allow_video=False)
        with transaction.atomic():
            page, _ = Page.objects.get_or_create(platform=d["platform"], handle=d["handle"])
            if Vouch.objects.filter(user=request.user, page=page).exists():
                raise ValidationError({"detail": "You've already vouched for this page."})
            Vouch.objects.create(user=request.user, page=page, comment=d.get("comment", ""), proof=content)
        return Response({"message": "Thank you. Your vouch will appear once a moderator has checked your proof."}, status=201)


class CheckRequestView(APIView):
    """Someone who hasn't bought yet asks 'is this page legit?'. It never changes a page's negative status."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CheckRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            page, _ = Page.objects.get_or_create(platform=d["platform"], handle=d["handle"])
            if CheckRequest.objects.filter(user=request.user, page=page).exists():
                raise ValidationError({"detail": "You've already asked about this page."})
            CheckRequest.objects.create(user=request.user, page=page, note=d.get("note", ""))
        refresh_label(page, reason="Check request")
        return Response({"message": "Thanks. This page is now listed as needing a check."}, status=201)


class CopyrightComplaintView(APIView):
    permission_classes = [IsVerifiedReporter]

    def post(self, request):
        s = CopyrightComplaintSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        page, _ = Page.objects.get_or_create(platform=d["platform"], handle=d["handle"])
        CopyrightComplaint.objects.create(
            complainant=request.user, page=page, original_url=d["original_url"],
            infringing_url=d["infringing_url"], description=d["description"],
        )
        return Response({"message": "Your complaint was received and will be reviewed."}, status=201)
