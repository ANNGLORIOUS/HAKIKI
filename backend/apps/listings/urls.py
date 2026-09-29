from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.SearchView.as_view()),
    path("pages/<str:platform>/<str:handle>/", views.PageDetailView.as_view()),
    path("pages/<str:platform>/<str:handle>/claim/", views.ClaimView.as_view()),
]
