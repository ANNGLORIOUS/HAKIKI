from django.contrib import admin

from apps.accounts.models import User
from apps.moderation.models import ModerationAction

from .models import OwnershipClaim, Page, PageLabelHistory, PagePayment, PaymentIdentifier
from .services import refresh_label


class PaymentInline(admin.TabularInline):
    model = PagePayment
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("handle", "platform", "public_label", "verified_owner", "indexable", "created_at")
    list_filter = ("platform", "public_label", "verified_owner", "indexable")
    search_fields = ("handle",)
    inlines = [PaymentInline]


@admin.register(PaymentIdentifier)
class PaymentIdentifierAdmin(admin.ModelAdmin):
    # Full values are never shown in admin. Revealing must go through an audited action.
    list_display = ("id_type", "masked", "registered_name", "first_seen")
    exclude = ("value_encrypted", "value_hash")
    readonly_fields = ("masked",)


@admin.register(OwnershipClaim)
class OwnershipClaimAdmin(admin.ModelAdmin):
    list_display = ("page", "user", "code", "status", "created_at")
    list_filter = ("status",)
    actions = ["approve", "reject"]

    @admin.action(description="Approve (only after you saw the code in the page's bio)")
    def approve(self, request, queryset):
        for c in queryset.filter(status="pending"):
            page = c.page
            page.owner, page.verified_owner, page.claim_code = c.user, True, c.code
            page.save(update_fields=["owner", "verified_owner", "claim_code"])
            c.status = "approved"
            c.save(update_fields=["status"])
            if c.user.role == User.Role.REPORTER:
                c.user.role = User.Role.SELLER
                c.user.save(update_fields=["role"])
            ModerationAction.log(request.user, "claim.approved", c, {"status": "pending"}, {"status": "approved"})
            queryset.filter(page=page).exclude(pk=c.pk).update(status="rejected")

    @admin.action(description="Reject selected claims")
    def reject(self, request, queryset):
        for c in queryset:
            c.status = "rejected"
            c.save(update_fields=["status"])
            ModerationAction.log(request.user, "claim.rejected", c)


admin.site.register(PageLabelHistory)
