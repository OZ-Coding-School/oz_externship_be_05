from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.user.utils.social_login import (
    KakaoOAuthService,
    NaverOAuthService,
    parse_kakao_birthday,
    parse_naver_birthday,
)


class KakaoSocialLoginTests(TestCase):
    @patch("apps.user.views.social_login_views.KakaoOAuthService")
    def test_kakao_login_success(self, service_mock: Any) -> None:
        service: Any = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy_access"
        service.get_user_info.return_value = {
            "id": "test123",
            "kakao_account": {
                "profile": {"nickname": "건우의이름"},
                "email": "gunwoo@test.com",
                "gender": "male",
                "birthday": "0612",
            },
        }

        user: Any = get_user_model().objects.create_user(
            email="kakao@test.com",
            password="pw",
            name="카카오유저",
            birthday=date(2000, 1, 1),
        )
        service.get_or_create_user.return_value = user

        url = reverse("kakao-callback")

        session = self.client.session
        session["oauth_state_kakao"] = "test-state"
        session.save()

        resp = self.client.get(
            url,
            {"code": "abcd", "state": "test-state"},
            follow=False,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=kakao", resp["Location"])

        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)

    def test_kakao_login_requires_code(self) -> None:
        url = reverse("kakao-callback")
        resp = self.client.get(url, follow=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=kakao", resp["Location"])
        self.assertIn("is_success=False", resp["Location"])

    @patch("apps.user.views.social_login_views.KakaoOAuthService")
    def test_kakao_login_inactive_user(self, service_mock: Any) -> None:
        service: Any = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy"
        service.get_user_info.return_value = {
            "id": "test123",
            "kakao_account": {
                "profile": {"nickname": "건우의이름"},
                "email": "gunwoo@test.com",
                "gender": "male",
                "birthday": "0612",
            },
        }

        user: Any = get_user_model().objects.create_user(
            email="inactive@kakao.com",
            password="pw",
            name="비활성",
            birthday=date(2000, 1, 1),
        )
        user.is_active = False
        user.expire_at = date(2030, 1, 1)
        user.save()

        service.get_or_create_user.return_value = user

        url = reverse("kakao-callback")
        resp = self.client.get(url, {"code": "zzz"}, follow=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=kakao", resp["Location"])
        self.assertIn("is_success=False", resp["Location"])


class NaverSocialLoginTests(TestCase):
    @patch("apps.user.views.social_login_views.NaverOAuthService")
    def test_naver_login_success(self, service_mock: Any) -> None:
        service: Any = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy_token"
        service.get_user_info.return_value = {
            "id": "test1234",
            "email": "test@test.com",
            "name": "건우의미쿠네이버계정",
            "birthyear": "1000",
            "birthday": "0612",
        }

        user: Any = get_user_model().objects.create_user(
            email="naver@test.com",
            password="pw",
            name="네이버유저",
            birthday=date(2001, 2, 2),
        )
        service.get_or_create_user.return_value = user

        url = reverse("naver-callback")

        session = self.client.session
        session["oauth_state_naver"] = "test-state"
        session.save()

        resp = self.client.get(
            url,
            {"code": "11", "state": "test-state"},
            follow=False,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=naver", resp["Location"])
        self.assertIn("access_token", resp.cookies)
        self.assertIn("refresh_token", resp.cookies)

    def test_naver_requires_code_and_state(self) -> None:
        url = reverse("naver-callback")
        resp = self.client.get(url, {"code": "abc"}, follow=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=naver", resp["Location"])
        self.assertIn("is_success=False", resp["Location"])

    @patch("apps.user.views.social_login_views.NaverOAuthService")
    def test_naver_login_inactive_user(self, service_mock: Any) -> None:
        service: Any = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy"
        service.get_user_info.return_value = {
            "id": "test1234",
            "email": "test@test.com",
            "name": "건우의은밀한네이버계정",
            "birthyear": "1000",
            "birthday": "0612",
        }

        user: Any = get_user_model().objects.create_user(
            email="inactive@naver.com",
            password="pw",
            name="비활성유저",
            birthday=date(2005, 5, 5),
        )
        user.is_active = False
        user.expire_at = date(2029, 12, 31)
        user.save()

        service.get_or_create_user.return_value = user

        url = reverse("naver-callback")
        resp = self.client.get(url, {"code": "c", "state": "s"}, follow=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("provider=naver", resp["Location"])
        self.assertIn("is_success=False", resp["Location"])


class SocialLoginUtilsSimpleCoverageTests(TestCase):
    def test_parse_kakao_birthday(self) -> None:
        self.assertEqual(parse_kakao_birthday({"birthday": "0612"}), date(2000, 6, 12))
        self.assertIsNone(parse_kakao_birthday({"birthday": "061"}))
        self.assertIsNone(parse_kakao_birthday({}))

    def test_parse_naver_birthday(self) -> None:
        self.assertEqual(
            parse_naver_birthday({"birthyear": "1999", "birthday": "06-12"}),
            date(1999, 6, 12),
        )
        self.assertIsNone(parse_naver_birthday({"birthyear": "1999"}))
        self.assertIsNone(parse_naver_birthday({}))

    @override_settings(
        NAVER_CLIENT_ID="dummy",
        NAVER_CLIENT_SECRET="dummy",
        NAVER_REDIRECT_URI="http://test/callback",
    )
    @patch("apps.user.utils.social_login.requests.get")
    def test_naver_get_user_info_returns_response(self, get_mock: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.raise_for_status.return_value = None
        fake_resp.json.return_value = {"response": {"id": "naver1", "email": "a@a.com"}}
        get_mock.return_value = fake_resp

        service = NaverOAuthService()
        profile = service.get_user_info("token")
        self.assertEqual(profile["id"], "naver1")

    @override_settings(
        KAKAO_CLIENT_ID="dummy",
        KAKAO_REDIRECT_URI="http://test/callback",
    )
    @patch("apps.user.utils.social_login.requests.post")
    def test_kakao_get_access_token(self, post_mock: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.raise_for_status.return_value = None
        fake_resp.json.return_value = {"access_token": "kakao_token"}
        post_mock.return_value = fake_resp

        service = KakaoOAuthService()
        token = service.get_access_token("code")
        self.assertEqual(token, "kakao_token")
