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
    SignupEmailRequestSerializer,
    SMSRequestSerializer,
)
from apps.user.utils.sender import EmailSender, SMSSender


class SendEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SignupEmailRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailSender().send(serializer.validated_data["email"])
        return Response({"detail": "이메일 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK)


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = EmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = EmailSender().verify_code(
            serializer.validated_data["email"],
            serializer.validated_data["email_code"],
        )
        return Response({"detail": "이메일 인증에 성공하였습니다.", "email_token": token}, status=status.HTTP_200_OK)


class SendSMSVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SMSRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sender = SMSSender()
        except RuntimeError:
            Response({"error_detail": "SMS 전송 중 문제가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sender.send(serializer.validated_data["phone_number"])
        return Response({"detail": "SMS 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK)


class VerifySMSAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PhoneCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sender = SMSSender()
        except RuntimeError:
            Response({"error_detail": "SMS 인증에 문제가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        token = sender.verify_code(
            serializer.validated_data["phone_number"],
            serializer.validated_data["sms_code"],
        )
        return Response({"detail": "SMS 인증에 성공하였습니다.", "sms_token": token}, status=status.HTTP_200_OK)
