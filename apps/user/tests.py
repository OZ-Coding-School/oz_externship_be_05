from datetime import date
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.user.models import user as models

from django.urls import reverse
from rest_framework import status



class UserManagerTests(TestCase):
    def test_create_user_success_with_gen_nick(self) -> None:
        user = get_user_model().objects.create_user(
            email="miku@example.com",
            password="miku3939@!",
            name="하츠네미쿠",
            birthday=date(2007, 8, 31),
            gender=models.GenderChoices.FEMALE,
            phone_number="010-3939-3939",
        )
        self.assertEqual(user.email, "miku@example.com")
        self.assertEqual(user.name, "하츠네미쿠")
        self.assertTrue(user.nickname)  # 닉자동생성맛보기
        self.assertFalse(user.is_staff)
        self.assertEqual(user.role, models.RoleChoices.USER)

    def test_create_user_requires_email_password_name(self) -> None:
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="",
                password="im_oldguy_1234",
                name="이메일이없는노인",
                birthday=date(1930, 1, 1),
                gender=models.GenderChoices.MALE,
                phone_number="010-1234-1234",
            )
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="nopassword@example.com",
                password="",
                name="비밀이없는남자",
                birthday=date(2000, 1, 1),
                gender=models.GenderChoices.MALE,
                phone_number="010-1234-1234",
            )
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="이름없는여고생@example.com",
                password="no_name_1236",
                name="",
                birthday=date(2008, 1, 1),
                gender=models.GenderChoices.FEMALE,
                phone_number="010-1234-5678",
            )

    def test_create_superuser_sets_flags(self) -> None:
        admin = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="superscret",
            name="관리자임",
            birthday=date(2000, 1, 1),
            gender=models.GenderChoices.MALE,
            phone_number="010-0000-0000",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, models.RoleChoices.AD)

    # 중복닉 테스트
    @patch("apps.user.models.user.generate_nickname", return_value="신창섭")
    def test_create_user_fails_dupnick(self, generate_nickname_mock: Any) -> None:
        get_user_model().objects.create_user(
            email="maple@example.com",
            password="password123",
            name="닉네임선점하는메숭이",
            nickname="신창섭",
            birthday=date(2000, 1, 1),
            gender=models.GenderChoices.MALE,
            phone_number="010-1111-1111",
        )
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="new@example.com",
                password="password123",
                name="신규유저",
                birthday=date(2000, 1, 1),
                gender=models.GenderChoices.MALE,
                phone_number="010-2222-2222",
            )


class KakaoSocialLoginTests(TestCase):
    @patch("apps.user.views.social_login_views.KakaoOAuthService")
    def test_kakao_login_success(self, service_mock: Any) -> None:
        service = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy_access"
        service.get_user_info.return_value = {
            "id": "test123",
            "kakao_account": {
                "profile": {"nickname": "건우의이름"},
                "email": "gunwoo@test.com",
                "gender": "male",
                "birthday": "0612",
            }
        }

        user = get_user_model().objects.create_user(
            email="kakao@test.com",
            password="pw",
            name="카카오유저",
            birthday=date(2000, 1, 1),
        )
        service.get_or_create_user.return_value = user

        url = reverse("kakao-callback")
        resp = self.client.get(url, {"code": "abcd"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_kakao_login_requires_code(self) -> None:
        url = reverse("kakao-callback")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.user.views.social_login_views.KakaoOAuthService")
    def test_kakao_login_inactive_user(self, service_mock: Any) -> None:
        service = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy"
        service.get_user_info.return_value = {
            "id": "test123",
            "kakao_account": {
                "profile": {"nickname": "건우의이름"},
                "email": "gunwoo@test.com",
                "gender": "male",
                "birthday": "0612",
            }
        }

        user = get_user_model().objects.create_user(
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
        resp = self.client.get(url, {"code": "zzz"})

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", resp.data)
        self.assertIn("detail", resp.data["error_detail"])


class NaverSocialLoginTests(TestCase):
    @patch("apps.user.views.social_login_views.NaverOAuthService")
    def test_naver_login_success(self, service_mock: Any) -> None:
        service = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy_token"
        service.get_user_info.return_value = {
            "response": {
                "id": "test1234",
                "email": "test@test.com",
                "name": "건우의미쿠네이버계정",
                "birthyear": "1000",
                "birthday": "0612"
            }
        }

        user = get_user_model().objects.create_user(
            email="naver@test.com",
            password="pw",
            name="네이버유저",
            birthday=date(2001, 2, 2),
        )
        service.get_or_create_user.return_value = user

        url = reverse("naver-callback")
        resp = self.client.get(url, {"code": "11", "state": "22"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_naver_requires_code_and_state(self) -> None:
        url = reverse("naver-callback")

        resp = self.client.get(url, {"code": "abc"}) 
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.user.views.social_login_views.NaverOAuthService")
    def test_naver_login_inactive_user(self, service_mock: Any) -> None:
        service = MagicMock()
        service_mock.return_value = service

        service.get_access_token.return_value = "dummy"
        service.get_user_info.return_value = {
            "response": {
                "id": "test1234",
                "email": "test@test.com",
                "name": "건우의은밀한네이버계정",
                "birthyear": "1000",
                "birthday": "0612"
            }
        }

        user = get_user_model().objects.create_user(
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
        resp = self.client.get(url, {"code": "c", "state": "s"})

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", resp.data)
        self.assertIn("detail", resp.data["error_detail"])
        