from datetime import date
from typing import ClassVar

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.user.models.user import RoleChoices, User
from apps.user.models.withdraw import Withdrawal


class AdminAccountListAPITests(APITestCase):
    admin: ClassVar[User]
    u1: ClassVar[User]
    u2: ClassVar[User]
    u3: ClassVar[User]
    url: ClassVar[str]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234!",
            name="Admin",
            nickname="adminnick",
            phone_number="01000000000",
            gender="M",
            birthday=date(1990, 1, 1),
            is_staff=True,
            is_superuser=True, 
            role=RoleChoices.AD,
        )

        cls.u1 = User.objects.create_user(
            email="user1@example.com",
            password="pass1234!",
            name="Kim",
            nickname="kimmy",
            phone_number="01011111111",
            gender="M",
            birthday=date(2000, 1, 1),
            is_active=True,
            role=RoleChoices.USER,
        )

        cls.u2 = User.objects.create_user(
            email="user2@example.com",
            password="pass1234!",
            name="Park",
            nickname="parky",
            phone_number="01022222222",
            gender="F",
            birthday=date(1995, 6, 10),
            is_active=False,
            role=RoleChoices.USER,
        )

        cls.u3 = User.objects.create_user(
            email="student@example.com",
            password="pass1234!",
            name="Lee",
            nickname="leelee",
            phone_number="01033333333",
            gender="F",
            birthday=date(2002, 12, 31),
            is_active=False,
            role=RoleChoices.ST,
        )
        Withdrawal.objects.create(
            user=cls.u3,
            reason="test",
            reason_detail="test",
            due_date=date(2099, 1, 1),
        )

        cls.url = reverse("admin-account-list")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.admin)

    def test_list_ok_returns_paginated_shape(self) -> None:
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        self.assertIn("results", resp.data)

    def test_search_filters_by_email_or_name_or_nickname(self) -> None:
        resp = self.client.get(self.url, {"search": "kim"})
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.data["results"]]
        self.assertIn(self.u1.id, ids)

    def test_filter_status_withdrew(self) -> None:
        resp = self.client.get(self.url, {"status": "withdrew"})
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.data["results"]]
        self.assertEqual(ids, [self.u3.id])

    def test_filter_status_deactivated_excludes_withdrew(self) -> None:
        resp = self.client.get(self.url, {"status": "deactivated"})
        self.assertEqual(resp.status_code, 200)
        ids = [row["id"] for row in resp.data["results"]]
        self.assertIn(self.u2.id, ids)
        self.assertNotIn(self.u3.id, ids)

    def test_invalid_role_returns_400(self) -> None:
        resp = self.client.get(self.url, {"role": "staf"})
        self.assertEqual(resp.status_code, 400)

    def test_pagination_page_size(self) -> None:
        resp = self.client.get(self.url, {"page_size": 2})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)
