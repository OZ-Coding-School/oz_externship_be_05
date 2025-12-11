from datetime import date

import requests
from django.conf import settings
from django.utils.crypto import get_random_string

from apps.user.models import SocialProvider, SocialUser, User


def parse_kakao_birthday(kakao_account: dict) -> date | None:
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


def parse_naver_birthday(naver_account: dict) -> date | None:
    birthyear = naver_account.get("birthyear")
    birthday = naver_account.get("birthday") 

    if not (birthyear and birthday and len(birthday) == 4):
        return None

    try:
        year = int(birthyear)
        month = int(birthday[:2])
        day = int(birthday[2:])
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

    def get_access_token(self, code: str) -> str:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        resp = requests.post(self.TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_or_create_user(self, kakao_profile: dict) -> User:
        kakao_id = str(kakao_profile["id"])
        kakao_account = kakao_profile.get("kakao_account", {}) or {}
        profile = kakao_account.get("profile", {}) or {}

        email = kakao_account.get("email")
        name = profile.get("nickname", "카카오유저")
        gender = kakao_account.get("gender")
        birthday_date = parse_kakao_birthday(kakao_account)
        profile_image_url = profile.get("profile_image_url") or profile.get("thumbnail_image_url") or None

        try:
            social_user = SocialUser.objects.get(
                provider=SocialProvider.KAKAO,
                provider_id=kakao_id,
            )
            return social_user.user
        except SocialUser.DoesNotExist:
            pass

        user = User.objects.create_user(
            email=email or f"kakao_{kakao_id}@example.com",
            password=get_random_string(20),
            name=name,
            gender="M" if gender == "male" else ("F" if gender == "female" else ""),
            birthday=birthday_date,
            profile_image_url=profile_image_url,
        )

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

    def get_access_token(self, code: str, state: str) -> str:
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "state": state,
        }
        resp = requests.get(self.TOKEN_URL, params=params)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        print("네이버 유저 데이터", data)

        return resp.json()

    def get_or_create_user(self, naver_profile: dict) -> User:
        resp = naver_profile.get("response", {}) or {}

        naver_id = str(resp.get("id"))
        email = resp.get("email")
        name = resp.get("name", "네이버유저")

        try:
            social_user = SocialUser.objects.get(
                provider=SocialProvider.NAVER,
                provider_id=naver_id,
            )
            return social_user.user
        except SocialUser.DoesNotExist:
            pass

        birthday_date = parse_naver_birthday(resp)

        user = User.objects.create_user(
            email=email or f"naver_{naver_id}@example.com",
            password=get_random_string(20),
            name=name,
            birthday=birthday_date,
        )

        SocialUser.objects.create(
            user=user,
            provider=SocialProvider.NAVER,
            provider_id=naver_id,
        )

        return user
