from typing import Literal, cast
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


def issue_token_pair(refresh: RefreshToken) -> Response:
    secure = getattr(settings, "SESSION_COOKIE_SECURE", False)
    samesite = cast(
        Literal["Lax", "Strict", "None", False] | None, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
    )
    response = Response({"access_token" : refresh.access_token},status=status.HTTP_200_OK)
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    return response