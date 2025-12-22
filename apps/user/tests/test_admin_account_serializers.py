from datetime import date
from typing import ClassVar

from django.test import TestCase

from apps.user.models import User
from apps.user.serializers.admin.accounts import (
    AdminAccountListSerializer,
)
from apps.user.tests.utils.serializer_asserts import SerializerAssertsMixin


class AdminAccountListSerialzierTests(SerializerAssertsMixin, TestCase):
    user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            name="name",
            nickname="nick",
            phone_number="01012345678",
            gender="M",
            birthday=date(2000, 1, 1),
        )

    def test_fields_exact(self) -> None:
        serializer = AdminAccountListSerializer(instance=self.user)
        data = serializer.data

        self.assert_keys_exact(
            data,
            {
                "id",
                "email",
                "nickname",
                "name",
                "birthday",
                "status",
                "role",
                "created_at",
            },
        )

    def test_values(self) -> None:
        data = AdminAccountListSerializer(instance=self.user).data
        expected = "active" if self.user.is_active else "inactive"
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["nickname"], self.user.nickname)
        self.assertEqual(data["name"], self.user.name)
        self.assert_date_str(data["birthday"], self.user.birthday)
        self.assertEqual(data["status"], expected)
        self.assertEqual(data["role"], self.user.role)
        self.assert_datetime_str(data["created_at"], self.user.created_at)

    def test_many_true(self) -> None:
        data = AdminAccountListSerializer(instance=[self.user], many=True).data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.user.id)
