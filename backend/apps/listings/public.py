"""Builds the public-safe view of pages and payment matches. Never exposes reporter identity,
full payment numbers, registered names, or unpublished reports."""
import re

from django.db.models import Count, Q

from apps.core.utils import hmac_hash, normalize_msisdn
from apps.submissions.models import Report

from .models import Page, PagePayment, PaymentIdentifier
from .text import DISCLAIMER, LABEL_EXPLAIN, LABEL_TEXT, SAFETY_TIPS, WHY_LISTED

VISIBLE = ["published", "disputed"]  # disputed reports stay visible while under review


def page_public(page, detail=True):
    visible = page.reports.filter(status__in=VISIBLE)
    data = {
        "platform": page.platform,
        "handle": page.handle,
        "profile_url": page.profile_url,
        "label": page.public_label,
        "label_text": LABEL_TEXT[page.public_label],
        "verified_owner": page.verified_owner,
        "reports_published": visible.count(),
        "vouches": page.vouches.filter(status="approved").count(),
    }
    if not detail:
        return data

    ids = list(PagePayment.objects.filter(page=page).values_list("identifier_id", flat=True))
    linked = (
        PagePayment.objects.filter(identifier_id__in=ids)
        .exclude(page=page)
        .filter(page__reports__status__in=VISIBLE)
        .values("page").distinct().count()
    )
    data.update({
        "explanation": LABEL_EXPLAIN[page.public_label],
        "why_listed": WHY_LISTED,
        "reports_with_supported_evidence": visible.filter(evidence__status="supported").distinct().count(),
        "categories": {r["category"]: r["n"] for r in visible.values("category").annotate(n=Count("id"))},
        "check_requests": page.check_requests.count(),
        "linked_pages_count": linked,
        "payment_identifiers": [
            {"type": p.identifier.id_type, "masked": p.identifier.masked}
            for p in page.payments.select_related("identifier")
            if p.identifier.id_type != "whatsapp"
        ],
        "disputed": page.public_label == Page.Label.DISPUTED,
        "indexable": page.indexable,
        "last_reviewed": page.last_reviewed_at or page.label_updated_at,
        "safety_tips": SAFETY_TIPS,
        "disclaimer": DISCLAIMER,
    })
    return data


def search_handle(q, platform=None):
    from apps.core.utils import SOCIAL_HOSTS, parse_social
    from urllib.parse import urlparse

    if not platform and ("/" in q or "." in q.split("?")[0]):
        host = (urlparse(q if "://" in q else "https://" + q).hostname or "").lower()
        for plat, hosts in SOCIAL_HOSTS.items():
            if any(host == h or host.endswith("." + h) for h in hosts):
                platform = plat
    handle = parse_social(platform or "", q) if platform else q.strip().lstrip("@").lower()
    qs = Page.objects.filter(handle=handle)
    if platform:
        qs = qs.filter(platform=platform)
    results = [page_public(p) for p in qs[:10]]
    return {
        "query_type": "handle",
        "query": handle,
        "found": bool(results),
        "results": results,
        "safety_tips": SAFETY_TIPS if not results else [],
        "message": "" if results else LABEL_EXPLAIN["no_reports"],
        "disclaimer": DISCLAIMER,
    }


def search_payment(q):
    """Exact-match only. Reveals counts of published reports and the public handles involved,
    never the number itself beyond what the searcher typed."""
    digits = re.sub(r"\D", "", q)
    if len(digits) < 5:
        raise ValueError("Enter the full phone number, Till number, Paybill or account number.")
    candidates = []
    try:
        msisdn = normalize_msisdn(q)
        candidates += [("send_money", msisdn), ("whatsapp", msisdn)]
    except ValueError:
        pass
    candidates += [(t, digits) for t in ("till", "paybill", "bank")]
    hashes = [hmac_hash("%s:%s" % (t, v)) for t, v in candidates]
    idents = PaymentIdentifier.objects.filter(value_hash__in=hashes)
    reports = Report.objects.filter(status__in=VISIBLE).filter(
        Q(payment_identifier__in=idents) | Q(whatsapp_identifier__in=idents)
    ).distinct()
    n = reports.count()
    pages = Page.objects.filter(reports__in=reports).distinct()[:10] if n else []
    return {
        "query_type": "payment",
        "matched": n > 0,
        "report_count": n,
        "page_count": Page.objects.filter(reports__in=reports).distinct().count() if n else 0,
        "pages": [page_public(p, detail=False) for p in pages],
        "message": (
            "This number appears in %d published user report%s." % (n, "" if n == 1 else "s")
            if n else "No published reports match this number. This does not mean it is safe."
        ),
        "safety_tips": SAFETY_TIPS if not n else [],
        "disclaimer": DISCLAIMER,
    }
