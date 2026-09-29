from django.urls import path

from . import views

urlpatterns = [
    path("reports/<int:report_id>/dispute/", views.DisputeCreateView.as_view()),
    path("disputes/<int:dispute_id>/appeal/", views.AppealCreateView.as_view()),
    path("moderation/disputes/<int:dispute_id>/decide/", views.DisputeDecideView.as_view()),
    path("moderation/appeals/<int:appeal_id>/decide/", views.AppealDecideView.as_view()),
]
