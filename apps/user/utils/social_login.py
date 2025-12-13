from datetime import date
from typing import Any, cast

import requests
from django.conf import settings
from django.utils.crypto import get_random_string
from rest_framework.exceptions import ValidationError

from apps.user.models import SocialProvider, SocialUser, User


def parse_kakao_birthday(kakao_account: dict[str, Any]) -> date | None:
    birthday = kakao_account.get("birthday")

    if not (birthday and len(birthday) == 4):
        return None

    month = int(birthday[:2])
    day = int(birthday[2:])
    year = 2000

    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_naver_birthday(naver_account: dict[str, Any]) -> date | None:
    birthyear = naver_account.get("birthyear")
    birthday = naver_account.get("birthday")

    if not (birthyear and birthday):
        return None
    try:
        year = int(birthyear)
        month = int(birthday[:2])
        day = int(birthday[3:])
        return date(year, month, day)
    except ValueError:
        return None


class KakaoOAuthService:
    AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def __init__(self) -> None:
        self.client_id = settings.KAKAO_CLIENT_ID
        self.redirect_uri = settings.KAKAO_REDIRECT_URI

    # 토큰 받아옴
    def get_access_token(self, code: str) -> str:
        data = {
            "grant_type": "authorization_code",
            "client_id": cast(str, self.client_id),
            "redirect_uri": cast(str, self.redirect_uri),
            "code": code,
        }
        resp: requests.Response = requests.post(self.TOKEN_URL, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        return str(token_data["access_token"])

    # 유저 정보 받아옴
    def get_user_info(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp: requests.Response = requests.get(self.USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        profile_data: dict[str, Any] = resp.json()
        return profile_data

    def get_or_create_user(self, kakao_profile: dict[str, Any]) -> User:
        kakao_id = str(kakao_profile["id"])
        kakao_account = kakao_profile.get("kakao_account", {}) or {}
        profile = kakao_account.get("profile", {}) or {}

        email: str | None = kakao_account.get("email")
        if not email:
            raise ValidationError({"email": ["카카오 계정 이메일 제공에 동의가 필요합니다."]})

        name = profile.get("nickname", "카카오유저")
        gender = kakao_account.get("gender")
        birthday_date = parse_kakao_birthday(kakao_account)
        profile_image_url = profile.get("profile_image_url") or profile.get("thumbnail_image_url") or None

        # 카카오 유저가 존재하면 유저 바로 줘버려
        social_user = (
            SocialUser.objects.filter(
                provider=SocialProvider.KAKAO,
                provider_id=kakao_id,
            )
            .select_related("user")
            .first()
        )
        if social_user:
            return social_user.user

        # 이메일 유저가 존재하면 카카오로 연결
        user = User.objects.filter(email__iexact=email).first()
        if user:
            SocialUser.objects.get_or_create(
                user=user,
                provider=SocialProvider.KAKAO,
                provider_id=kakao_id,
            )
            return user

        # 유저가 없으면 생성하고 연결
        user = User.objects.create_user(
            email=email,
            password=get_random_string(20),
            name=name,
            gender="M" if gender == "male" else ("F" if gender == "female" else ""),
            birthday=birthday_date,
            profile_image_url=profile_image_url,
        )

        user.set_unusable_password()
        user.save(update_fields=["password"])

        SocialUser.objects.create(
            user=user,
            provider=SocialProvider.KAKAO,
            provider_id=kakao_id,
        )

        return user


class NaverOAuthService:
    TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
    USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"

    def __init__(self) -> None:
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.redirect_uri = settings.NAVER_REDIRECT_URI

    # 토큰 받아옴
    def get_access_token(self, code: str, state: str) -> str:
        params = {
            "grant_type": "authorization_code",
            "client_id": cast(str, self.client_id),
            "client_secret": cast(str, self.client_secret),
            "redirect_uri": cast(str, self.redirect_uri),
            "code": code,
            "state": state,
        }
        resp: requests.Response = requests.get(self.TOKEN_URL, params=params)
        resp.raise_for_status()
        token_data = resp.json()
        return str(token_data["access_token"])

    # 유저정보 가져옴
    def get_user_info(self, access_token: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USER_INFO_URL, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        profile: dict[str, Any] | None = data.get("response")
        if not profile:
            raise ValidationError({"naver": ["네이버 프로필 응답이 비어있습니다."]})

        return profile

    # 유저 생성
    def get_or_create_user(self, naver_profile: dict[str, Any]) -> User:
        naver_id = str(naver_profile.get("id"))
        email = naver_profile.get("email")
        if not email:
            raise ValidationError({"email": ["네이버 계정 이메일 제공에 동의가 필요합니다."]})

        name = naver_profile.get("name", "네이버유저")
        birthday_date = parse_naver_birthday(naver_profile)

        # 네이버 유저가 존재하면 유저 바로 줘버려
        social_user = (
            SocialUser.objects.filter(
                provider=SocialProvider.NAVER,
                provider_id=naver_id,
            )
            .select_related("user")
            .first()
        )

        if social_user:
            return social_user.user

        # 이메일 유저가 존재하면 카카오로 연결
        user = User.objects.filter(email__iexact=email).first()
        if user:
            SocialUser.objects.get_or_create(
                user=user,
                provider=SocialProvider.NAVER,
                provider_id=naver_id,
            )
            return user

        # 유저가 없으면 생성하고 연결
        user = User.objects.create_user(
            email=email,
            password=get_random_string(20),
            name=name,
            birthday=birthday_date,
        )

        user.set_unusable_password()
        user.save(update_fields=["password"])

        SocialUser.objects.create(
            user=user,
            provider=SocialProvider.NAVER,
            provider_id=naver_id,
        )

        return user
