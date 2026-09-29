from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path("auth/email/send/", views.EmailSendView.as_view()),
    path("auth/email/verify/", views.EmailVerifyView.as_view()),
    path("auth/phone/send/", views.PhoneSendView.as_view()),
    path("auth/phone/verify/", views.PhoneVerifyView.as_view()),
]
