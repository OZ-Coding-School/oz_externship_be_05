from datetime import date

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.user.models.user import RoleChoices


class CreateUserCommandTests(TestCase):
    def test_createuser_creates_user(self) -> None:
        call_command(
            "createuser",
            "user@example.com",
            "password123",
            "User Name",
            "01012345678",
            "M",
            "2000-01-02",
            "--nickname",
            "usernick",
            "--role",
            RoleChoices.USER,
        )

        user = get_user_model().objects.get(email="user@example.com")
        self.assertEqual(user.name, "User Name")
        self.assertEqual(user.nickname, "usernick")
        self.assertEqual(user.phone_number, "01012345678")
        self.assertEqual(user.gender, "M")
        self.assertEqual(user.birthday, date(2000, 1, 2))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, RoleChoices.USER)

    def test_createuser_superuser_flag(self) -> None:
        call_command(
            "createuser",
            "admin@example.com",
            "password123",
            "Admin User",
            "01099999999",
            "F",
            "1999-12-31",
            "--superuser",
        )

        user = get_user_model().objects.get(email="admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, RoleChoices.AD)
