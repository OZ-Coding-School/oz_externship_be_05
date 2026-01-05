from typing import Literal, cast

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def issue_token_pair(refresh: RefreshToken) -> Response:
    secure = getattr(settings, "SESSION_COOKIE_SECURE", True)
    samesite = cast(Literal["Lax", "Strict", "None", False] | None, getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax"))
    response = Response({"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)
    if settings.DEBUG:
        secure = True
        samesite = "None"
    response.set_cookie(
        "refresh_token",
        str(refresh),
        domain=settings.COOKIE_DOMAIN,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    return response
