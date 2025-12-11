from django.shortcuts import redirect
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.user.serializers.social_profile import (
    NaverProfileSerializer,
    KakaoProfileSerializer,
)
from apps.user.utils.social_login import (
    KakaoOAuthService,
    NaverOAuthService,
)


class KakaoLoginStartAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        SCOPES = [
            "profile_nickname",
            "profile_image",
            "account_email",
            "gender",
            "birthday",
            "age_range",
        ]

        scope_str = ",".join(SCOPES)

        authorize_url = (
            f"{KakaoOAuthService.AUTHORIZE_URL}"
            f"?response_type=code"
            f"&client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            f"&scope={scope_str}"
        )
        return redirect(authorize_url)


class NaverLoginStartAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponseRedirect:
        import uuid

        state = uuid.uuid4().hex

        authorize_url = (
            f"https://nid.naver.com/oauth2.0/authorize"
            f"?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state={state}"
        )
        return redirect(authorize_url)


class KakaoCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        code: str | None = request.query_params.get("code")
        if not code:
            return HttpResponseBadRequest("code is required")

        service = KakaoOAuthService()
        access_token: str = service.get_access_token(code)
        profile: dict = service.get_user_info(access_token)

        serializer = KakaoProfileSerializer(data=profile)
        serializer.is_valid(raise_exception=True)

        user = service.get_or_create_user(profile)

        if not user.is_active:
            raise APIException(
                {
                    "error_detail": {
                        "detail": "탈퇴 신청한 계정입니다.",
                        "expire_at": getattr(user, "expire_at", None),
                    }
                },
                status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_200_OK,
        )


class NaverCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        code: str | None = request.query_params.get("code")
        state: str | None = request.query_params.get("state")

        if not code or not state:
            return Response(
                {"error_detail": {"code": ["code and state are required"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = NaverOAuthService()
        access_token: str = service.get_access_token(code, state)
        profile: dict = service.get_user_info(access_token)

        serializer = NaverProfileSerializer(data=profile.get("response", {}))
        serializer.is_valid(raise_exception=True)

        user = service.get_or_create_user(serializer.validated_data)

        if not user.is_active:
            raise APIException(
                {
                    "error_detail": {
                        "detail": "탈퇴 신청한 계정입니다.",
                        "expire_at": getattr(user, "expire_at", None),
                    }
                },
                status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_200_OK,
        )