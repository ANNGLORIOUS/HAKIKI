from django.conf import settings
from django.utils import timezone

from .models import Page, PageLabelHistory

VOUCH_MIN = 2


def compute_label(page: Page) -> str:
    """Evidence-based label. A single report never produces a negative public label."""
    L = Page.Label
    reports = page.reports.all()
    if reports.filter(status="disputed").exists():
        return L.DISPUTED
    published = reports.filter(status="published")
    supported = published.filter(evidence__status="supported").distinct()
    independent = supported.values("reporter").distinct().count()
    vouches = page.vouches.filter(status="approved").count()

    if independent >= settings.REPORT_THRESHOLD:
        return L.MIXED if vouches >= VOUCH_MIN else L.REPORTED_MULTIPLE
    if published.exists() or reports.filter(status__in=["submitted", "screening", "under_review"]).exists():
        return L.MIXED if vouches >= VOUCH_MIN and published.exists() else L.REPORTS_REVIEW
    if vouches >= VOUCH_MIN:
        return L.VOUCHED
    if page.check_requests.exists():
        return L.NEEDS_CHECKING
    if reports.filter(status="resolved").exists():
        return L.RESOLVED
    return L.NO_REPORTS


def refresh_label(page: Page, changed_by=None, reason: str = "") -> Page:
    new = compute_label(page)
    if new != page.public_label:
        page.public_label = new
        page.label_updated_at = timezone.now()
        page.indexable = new in (Page.Label.REPORTED_MULTIPLE, Page.Label.VOUCHED, Page.Label.MIXED)
        page.save(update_fields=["public_label", "label_updated_at", "indexable"])
        PageLabelHistory.objects.create(page=page, label=new, changed_by=changed_by, reason=reason or "Recomputed")
    return page
