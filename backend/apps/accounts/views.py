import logging

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OTP, User
from .otp import check_otp, create_otp, deliver
from .serializers import CodeSerializer, LoginSerializer, PhoneSerializer, RegisterSerializer, user_payload

logger = logging.getLogger(__name__)


def _auth_response(user, code=status.HTTP_200_OK):
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": user_payload(user)}, status=code)


def _send(user, channel, target):
    code = create_otp(user, channel, target)
    try:
        deliver(channel, target, code)
    except Exception:  # never reveal provider errors; user can request a new code
        logger.exception("Could not deliver %s code", channel)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"]
        user = User.objects.create_user(username=email, email=email, password=s.validated_data["password"])
        _send(user, OTP.Channel.EMAIL, email)
        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = authenticate(username=s.validated_data["email"].strip().lower(), password=s.validated_data["password"])
        if not user or not user.is_active:
            return Response({"detail": "Incorrect email or password."}, status=status.HTTP_400_BAD_REQUEST)
        return _auth_response(user)


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(user_payload(request.user))


class EmailSendView(APIView):
    throttle_scope = "otp"

    def post(self, request):
        if request.user.email_verified:
            return Response({"detail": "Email already verified."})
        _send(request.user, OTP.Channel.EMAIL, request.user.email)
        return Response({"detail": "We sent a 6-digit code to your email."})


class EmailVerifyView(APIView):
    def post(self, request):
        s = CodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not check_otp(request.user, OTP.Channel.EMAIL, s.validated_data["code"]):
            return Response({"detail": "That code is wrong or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.email_verified = True
        request.user.save(update_fields=["email_verified"])
        return Response(user_payload(request.user))


class PhoneSendView(APIView):
    throttle_scope = "otp"

    def post(self, request):
        s = PhoneSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        phone = s.validated_data["phone"]
        if User.objects.filter(phone=phone, phone_verified=True).exclude(pk=request.user.pk).exists():
            return Response({"phone": ["This number is already linked to another account."]}, status=status.HTTP_400_BAD_REQUEST)
        _send(request.user, OTP.Channel.PHONE, phone)
        return Response({"detail": "We sent a 6-digit code by SMS."})


class PhoneVerifyView(APIView):
    def post(self, request):
        s = CodeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        otp = check_otp(request.user, OTP.Channel.PHONE, s.validated_data["code"])
        if not otp:
            return Response({"detail": "That code is wrong or has expired."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(phone=otp.target, phone_verified=True).exclude(pk=request.user.pk).exists():
            return Response({"detail": "This number is already linked to another account."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.phone = otp.target
        request.user.phone_verified = True
        request.user.save(update_fields=["phone", "phone_verified"])
        return Response(user_payload(request.user))
