import re
import secrets

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils import parse_social

from .models import OwnershipClaim, Page, Platform
from .public import page_public, search_handle, search_payment
from .text import DISCLAIMER, LABEL_EXPLAIN, SAFETY_TIPS


class SearchView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "search"

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        platform = request.query_params.get("platform") or None
        if not q or len(q) > 200:
            return Response({"detail": "Enter a handle, link, phone number or Till number."}, status=400)
        if platform and platform not in Platform.values:
            return Response({"detail": "Unknown platform."}, status=400)
        try:
            if re.fullmatch(r"[\d\s+\-()]{5,}", q):
                return Response(search_payment(q))
            return Response(search_handle(q, platform))
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)


class PageDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, platform, handle):
        page = Page.objects.filter(platform=platform, handle=handle.lower().lstrip("@")).first()
        if not page:
            return Response({
                "platform": platform, "handle": handle, "found": False,
                "label": "no_reports", "label_text": "No reports yet",
                "explanation": LABEL_EXPLAIN["no_reports"],
                "safety_tips": SAFETY_TIPS, "disclaimer": DISCLAIMER,
            })
        return Response(dict(page_public(page), found=True))


class ClaimView(APIView):
    """Seller asks to be recognised as a page owner. A moderator checks the code in the bio."""

    def post(self, request, platform, handle):
        if platform not in Platform.values:
            raise ValidationError({"platform": "Unknown platform."})
        try:
            handle = parse_social(platform, handle)
        except ValueError as e:
            raise ValidationError({"handle": str(e)})
        with transaction.atomic():
            page, _ = Page.objects.get_or_create(platform=platform, handle=handle)
            if page.verified_owner:
                return Response({"detail": "This page already has a verified owner."}, status=status.HTTP_409_CONFLICT)
            claim, _ = OwnershipClaim.objects.get_or_create(
                page=page, user=request.user,
                defaults={"code": "HAKIKI-" + secrets.token_hex(3).upper()},
            )
        return Response({
            "code": claim.code,
            "status": claim.status,
            "instructions": "Add this code to your profile bio, then wait for a moderator to check it. "
                            "You can remove it after your ownership is confirmed.",
        }, status=status.HTTP_201_CREATED)
