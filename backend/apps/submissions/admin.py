from django.contrib import admin
from django.utils import timezone

from apps.listings.services import refresh_label
from apps.moderation.models import ModerationAction

from .models import CheckRequest, CopyrightComplaint, Evidence, Report, Vouch


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    fields = ("file", "kind", "status", "moderator_note")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "category", "status", "reporter", "created_at")
    list_filter = ("status", "category")
    search_fields = ("page__handle",)
    inlines = [EvidenceInline]
    actions = ["publish", "reject"]

    def _set(self, request, queryset, status, action):
        for r in queryset:
            before = {"status": r.status}
            r.status = status
            r.save(update_fields=["status", "updated_at"])
            ModerationAction.log(request.user, action, r, before, {"status": status})
            r.page.last_reviewed_at = timezone.now()
            r.page.save(update_fields=["last_reviewed_at"])
            refresh_label(r.page, request.user, action)

    @admin.action(description="Publish selected reports")
    def publish(self, request, queryset):
        self._set(request, queryset, Report.Status.PUBLISHED, "report.published")

    @admin.action(description="Reject selected reports")
    def reject(self, request, queryset):
        self._set(request, queryset, Report.Status.REJECTED, "report.rejected")

    def save_formset(self, request, form, formset, change):
        """Log every evidence status change and refresh the page label."""
        if formset.model is Evidence:
            for f in formset.forms:
                if f.instance.pk and "status" in f.changed_data:
                    old = Evidence.objects.get(pk=f.instance.pk).status
                    ModerationAction.log(request.user, "evidence.status", f.instance, {"status": old}, {"status": f.cleaned_data["status"]}, f.cleaned_data.get("moderator_note", ""))
        super().save_formset(request, form, formset, change)
        if formset.model is Evidence:
            refresh_label(form.instance.page, request.user, "Evidence reviewed")


@admin.register(Vouch)
class VouchAdmin(admin.ModelAdmin):
    list_display = ("page", "user", "status", "created_at")
    list_filter = ("status",)
    actions = ["approve", "reject"]

    def _set(self, request, queryset, status, action):
        for v in queryset:
            before = {"status": v.status}
            v.status = status
            v.save(update_fields=["status"])
            ModerationAction.log(request.user, action, v, before, {"status": status})
            refresh_label(v.page, request.user, action)

    @admin.action(description="Approve selected vouches")
    def approve(self, request, queryset):
        self._set(request, queryset, Vouch.Status.APPROVED, "vouch.approved")

    @admin.action(description="Reject selected vouches")
    def reject(self, request, queryset):
        self._set(request, queryset, Vouch.Status.REJECTED, "vouch.rejected")


admin.site.register(CheckRequest)
admin.site.register(CopyrightComplaint)
