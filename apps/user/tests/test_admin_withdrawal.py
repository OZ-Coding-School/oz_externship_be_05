from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.user.models.user import RoleChoices, User
from apps.user.models.withdraw import Withdrawal
from apps.user.views.admin.withdrawal import (
    AdminAccountWithdrawalListAPIView,
    AdminAccountWithdrawalRetrieveAPIView,
)


class AdminWithdrawalAPIMinimalTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass1234!",
            name="관리자",
            nickname="admin",
            phone_number="01000000000",
            birthday=date(1998, 1, 4),
            role=RoleChoices.AD,
        )

        self.u1 = User.objects.create_user(
            email="u1@example.com",
            password="pass1234!",
            name="유저1",
            nickname="u1",
            phone_number="01000000001",
            birthday=date(1999, 1, 1),
            role=RoleChoices.USER,
        )
        self.u2 = User.objects.create_user(
            email="u2@example.com",
            password="pass1234!",
            name="유저2",
            nickname="u2",
            phone_number="01000000002",
            birthday=date(1999, 1, 2),
            role=RoleChoices.ST,
        )

        self.w1 = Withdrawal.objects.create(
            user=self.u1,
            due_date=date.today() + timedelta(days=7),
        )
        self.w2 = Withdrawal.objects.create(
            user=self.u2,
            due_date=date.today() + timedelta(days=7),
        )

    def test_withdrawal_list_ok(self) -> None:
        request = self.factory.get("/admin/withdrawals")
        force_authenticate(request, user=self.admin)

        response = AdminAccountWithdrawalListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

    def test_withdrawal_list_filter_by_role_student(self) -> None:
        request = self.factory.get("/admin/withdrawals", {"role": "student"})
        force_authenticate(request, user=self.admin)

        response = AdminAccountWithdrawalListAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        results = response.data["results"]

        ids = {item["id"] for item in results}
        self.assertIn(self.w2.id, ids)
        self.assertNotIn(self.w1.id, ids)

    def test_withdrawal_retrieve_404(self) -> None:
        request = self.factory.get("/admin/withdrawals/999999")
        force_authenticate(request, user=self.admin)

        response = AdminAccountWithdrawalRetrieveAPIView.as_view()(request, withdrawal_id=999999)

        self.assertEqual(response.status_code, 404)

    def test_withdrawal_retrieve_ok(self) -> None:
        request = self.factory.get(f"/admin/withdrawals/{self.w1.id}")
        force_authenticate(request, user=self.admin)

        response = AdminAccountWithdrawalRetrieveAPIView.as_view()(request, withdrawal_id=self.w1.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.w1.id)

    def test_withdrawal_delete_cancel_ok(self) -> None:
        self.u1.is_active = False
        self.u1.save(update_fields=["is_active"])

        request = self.factory.delete(f"/admin/withdrawals/{self.w1.id}")
        force_authenticate(request, user=self.admin)

        response = AdminAccountWithdrawalRetrieveAPIView.as_view()(request, withdrawal_id=self.w1.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Withdrawal.objects.filter(id=self.w1.id).exists())

        self.u1.refresh_from_db()
        self.assertTrue(self.u1.is_active)
