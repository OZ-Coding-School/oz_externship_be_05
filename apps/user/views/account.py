from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import User, Withdrawal, WithdrawalReason
from apps.user.serializers.account import (
    ChangePasswordSerializer,
    ChangePhoneSerializer,
    LoginSerializer,
    NicknameCheckSerializer,
    SignupSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)
from apps.user.utils.tokens import issue_token_pair


class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = issue_token_pair(user)
        return Response({"detail": "회원가입이 완료되었습니다.", "tokens": tokens, "user": UserProfileSerializer(user).data}, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user: User = serializer.validated_data["user"]
        tokens = issue_token_pair(user)
        return Response({"tokens": tokens, "user": UserProfileSerializer(user).data}, status=status.HTTP_200_OK)


class RefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "refresh": serializer.validated_data["refresh"],
                "access": serializer.validated_data["access"],
            },
            status=status.HTTP_200_OK,
        )


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        payload = request.data
        reason_value = payload.get("reason") or WithdrawalReason.OTHER
        if reason_value not in WithdrawalReason.values:
            reason_value = WithdrawalReason.OTHER
        detail = payload.get("reason_detail") or "회원 탈퇴를 요청했습니다."
        grace_days = getattr(settings, "WITHDRAWAL_GRACE_DAYS", 14)
        due_date = timezone.now().date() + timedelta(days=grace_days)

        Withdrawal.objects.update_or_create(
            user=request.user,
            defaults={"reason": reason_value, "reason_detail": detail, "due_date": due_date},
        )
        request.user.is_active = False
        request.user.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckNicknameAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = NicknameCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nickname = serializer.validated_data["nickname"]
        exists = User.objects.filter(nickname__iexact=nickname).exists()
        return Response({"available": not exists}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user: User = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return Response({"detail": "비밀번호가 변경되었습니다."}, status=status.HTTP_200_OK)


class ChangePhoneAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = ChangePhoneSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response({"phone_number": request.user.phone_number}, status=status.HTTP_200_OK)
