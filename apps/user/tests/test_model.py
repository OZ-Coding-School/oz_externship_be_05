from datetime import date
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.user.models import user as models


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
