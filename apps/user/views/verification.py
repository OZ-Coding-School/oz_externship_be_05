from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.serializers.verification import (
    EmailCodeSerializer,
    PhoneCodeSerializer,
    SMSRequestSerializer,
    SignupEmailRequestSerializer,
)
from apps.user.utils.sender import EmailSender, SMSSender


class SignupSendEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SignupEmailRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailSender().send(serializer.validated_data["email"])
        return Response({"detail": "Verification code sent to email."}, status=status.HTTP_200_OK)


class SignupVerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = EmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = EmailSender().verify_code(
            serializer.validated_data["email"],
            serializer.validated_data["verify_code"],
        )
        return Response({"email_token": token}, status=status.HTTP_200_OK)


class SendSMSVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sender = SMSSender()
        except RuntimeError as exc:
            raise ValidationError(str(exc)) from exc
        sender.send(serializer.validated_data["phone_number"])
        return Response({"detail": "Verification code sent via SMS."}, status=status.HTTP_200_OK)


class VerifySMSAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PhoneCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sender = SMSSender()
        except RuntimeError as exc:
            raise ValidationError(str(exc)) from exc
        token = sender.verify_code(
            serializer.validated_data["phone_number"],
            serializer.validated_data["verify_code"],
        )
        return Response({"sms_token": token}, status=status.HTTP_200_OK)
