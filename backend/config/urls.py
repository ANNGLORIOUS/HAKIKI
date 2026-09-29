from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.listings.urls")),
    path("api/", include("apps.submissions.urls")),
    path("api/", include("apps.moderation.urls")),
]
# Local development only: serves uploaded files. In production, evidence lives in private
# S3-compatible storage and is only reachable through signed, expiring links.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
