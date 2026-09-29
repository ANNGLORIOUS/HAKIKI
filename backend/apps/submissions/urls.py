from django.urls import path

from . import views

urlpatterns = [
    path("reports/", views.ReportCreateView.as_view()),
    path("me/reports/", views.MyReportsView.as_view()),
    path("vouches/", views.VouchCreateView.as_view()),
    path("check-requests/", views.CheckRequestView.as_view()),
    path("copyright-complaints/", views.CopyrightComplaintView.as_view()),
]
