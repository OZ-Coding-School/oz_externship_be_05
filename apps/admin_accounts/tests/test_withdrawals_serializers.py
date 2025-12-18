from datetime import timedelta
from typing import ClassVar

from django.test import TestCase
from django.utils import timezone

from apps.admin_accounts.serializers.withdrawals import (
    AdminAccountWithdrawalListSerializer,
    AdminAccountWithdrawalRetrieveSerializer,
)
from apps.admin_accounts.tests.utils.factories import (
    make_cohort,
    make_course,
    make_user,
)
from apps.user.models.role import CohortStudent
from apps.user.models.user import User
from apps.user.models.withdraw import Withdrawal


class WithdrawalSerializersTests(TestCase):
    user: ClassVar[User]
    withdrawal: ClassVar[Withdrawal]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = make_user(email="w@test.com", nickname="wnick")
        cls.withdrawal = Withdrawal.objects.create(
            user=cls.user,
            reason="OTHER",
            reason_detail="사유",
            due_date=timezone.now().date() + timedelta(days=7),
        )

    def test_list_serializer_fields(self) -> None:
        data = AdminAccountWithdrawalListSerializer(instance=self.withdrawal).data
        self.assertEqual(set(data.keys()), {"id", "user", "reason", "reason_display", "withdrawn_at"})
        self.assertEqual(data["reason"], self.withdrawal.reason)
        self.assertEqual(data["reason_display"], self.withdrawal.get_reason_display())

    def test_retrieve_serializer_assigned_courses(self) -> None:
        course = make_course(name="Django", tag="BE")
        cohort = make_cohort(course=course, number=1)
        CohortStudent.objects.create(user=self.user, cohort=cohort)

        data = AdminAccountWithdrawalRetrieveSerializer(instance=self.withdrawal).data
        self.assertIn("assigned_courses", data)
        self.assertEqual(len(data["assigned_courses"]), 1)

        item = data["assigned_courses"][0]
        self.assertIn("course", item)
        self.assertIn("cohort", item)
        self.assertEqual(item["course"]["id"], course.id)
        self.assertEqual(item["cohort"]["id"], cohort.id)
