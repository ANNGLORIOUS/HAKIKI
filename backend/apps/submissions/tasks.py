from celery import shared_task


@shared_task
def screen_report(report_id):
    """Automated screening: notes anything a moderator should look at, then moves the report
    to 'under review'. It never publishes or rejects a report by itself."""
    from django.utils import timezone

    from apps.listings.services import refresh_label
    from apps.moderation.models import ModerationAction

    from .models import Report

    report = Report.objects.select_related("reporter", "page").filter(pk=report_id).first()
    if not report or report.status != Report.Status.SUBMITTED:
        return
    report.status = Report.Status.SCREENING
    report.save(update_fields=["status", "updated_at"])

    notes = []
    user = report.reporter
    if (timezone.now() - user.date_joined).total_seconds() < 24 * 3600:
        notes.append("Reporter account is less than 24 hours old")
    if Report.objects.filter(reporter=user, status=Report.Status.REJECTED).count() >= 3:
        notes.append("Reporter has 3 or more rejected reports")
    if user.reputation < 0:
        notes.append("Reporter has negative reputation")
    page = report.page
    if page.owner_id and page.owner_id == user.pk:
        notes.append("Reporter owns the reported page")
    if Report.objects.filter(page=page, reporter=user).exclude(pk=report.pk).exists():
        notes.append("Reporter has another report on this page")
    if report.payment_identifier_id:
        others = (
            Report.objects.filter(payment_identifier_id=report.payment_identifier_id)
            .exclude(page=page).values("page").distinct().count()
        )
        if others:
            notes.append("Payment identifier also appears on %d other page(s)" % others)

    report.status = Report.Status.UNDER_REVIEW
    report.save(update_fields=["status", "updated_at"])
    ModerationAction.log(
        None, "report.screened", report,
        before={"status": "submitted"}, after={"status": "under_review"},
        reason="; ".join(notes) or "Passed automated screening",
    )
    refresh_label(report.page, reason="Report received")
