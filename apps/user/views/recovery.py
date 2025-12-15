from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import Withdrawal
from apps.user.serializers.recovery import (
    FindEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    RestoreSerializer,
)
from apps.user.serializers.verification import EmailCodeSerializer
from apps.user.utils.sender import EmailSender
from apps.user.utils.tokens import issue_token_pair


class RestoreSendEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        EmailSender().send(email)
        return Response({"detail": "인증 코드가 이메일로 발송되었습니다."}, status=status.HTTP_200_OK)


class RestoreAPIView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request: Request) -> Response:
        serializer = RestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        Withdrawal.objects.filter(user=user).delete()
        return Response({"detail": "계정이 복구되었습니다."}, status=status.HTTP_200_OK)


class FindEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = FindEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emails = serializer.validated_data["emails"]
        masked = [EmailSender.mask_email(email) for email in emails]
        return Response({"emails": masked}, status=status.HTTP_200_OK)


class FindPasswordSendEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        EmailSender().send(serializer.validated_data["email"])
        return Response({"detail": "인증 코드가 이메일로 발송되었습니다."}, status=status.HTTP_200_OK)


class FindPasswordVerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = EmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = EmailSender().verify_code(
            serializer.validated_data["email"],
            serializer.validated_data["verify_code"],
        )
        return Response({"email_token": token}, status=status.HTTP_200_OK)


class FindPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = issue_token_pair(user)
        return Response({"detail": "비밀번호가 재설정되었습니다.", "tokens": tokens}, status=status.HTTP_200_OK)
