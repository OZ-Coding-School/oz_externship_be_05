from datetime import date, timedelta
from typing import ClassVar

from django.test import TestCase
from django.utils import timezone

from apps.admin_accounts.serializers.accounts import (
    AdminAccountListSerializer,
    AdminAccountResponseSerializer,
    AdminAccountRetrieveSerializer,
    AdminAccountRoleUpdateSerializer,
    AdminAccountUpdateSerializer,
)
from apps.admin_accounts.tests.utils.serializer_asserts import SerializerAssertsMixin
from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User
from apps.user.models.role import CohortStudent

ROLE_USER = {"U", "AD"}
ROLE_COHORT = {"TA", "ST"}
ROLE_COURSES = {"OM", "LC"}


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


class AdminAccountRetrieveSerializerTests(SerializerAssertsMixin, TestCase):
    user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="b@test.com",
            password="pass1234!!",
            nickname="nick2",
            name="name2",
            phone_number="01012345678",
            birthday=date(1999, 12, 31),
            gender="M",
        )

    def test_fields_exact(self) -> None:
        data = AdminAccountRetrieveSerializer(instance=self.user).data

        self.assert_keys_exact(
            data,
            {
                "id",
                "email",
                "nickname",
                "name",
                "phone_number",
                "birthday",
                "gender",
                "status",
                "role",
                "profile_image_url",
                "assigned_courses",
                "created_at",
            },
        )

    def test_assigned_courses_empty_when_no_cohortstudent(self) -> None:
        data = AdminAccountRetrieveSerializer(instance=self.user).data
        self.assertEqual(data["assigned_courses"], [])

    def test_assigned_courses_returns_course_and_cohort(self) -> None:
        course = Course.objects.create(name="Django", tag="BE", description="desc")
        today = timezone.now().date()
        cohort1 = Cohort.objects.create(
            course=course,
            number=1,
            max_student=30,
            start_date=today,
            end_date=today + timedelta(days=30),
        )
        cohort2 = Cohort.objects.create(
            course=course,
            number=2,
            max_student=30,
            start_date=today,
            end_date=today + timedelta(days=30),
        )

        CohortStudent.objects.create(user=self.user, cohort=cohort1)
        CohortStudent.objects.create(user=self.user, cohort=cohort2)

        data = AdminAccountRetrieveSerializer(instance=self.user).data
        self.assertEqual(len(data["assigned_courses"]), 2)

        for item in data["assigned_courses"]:
            self.assertIn("course", item)
            self.assertIn("cohort", item)
            self.assertIn("id", item["course"])
            self.assertIn("id", item["cohort"])


class AdminAccountUpdateSerializerTests(TestCase):
    user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="u@test.com",
            password="pass1234!!",
            nickname="oldnick",
            name="oldname",
            phone_number="01011112222",
            birthday=date(2000, 1, 2),
            gender="M",
        )

    def test_update_serializer_fields(self) -> None:
        s = AdminAccountUpdateSerializer(instance=self.user)
        self.assertEqual(
            set(s.fields.keys()),
            {"nickname", "name", "phone_number", "birthday", "gender", "status", "profile_image_url"},
        )
        self.assertTrue(s.fields["status"].write_only)
        self.assertNotIn("status", s.data)

    def test_partial_update_success(self) -> None:
        payload = {"nickname": "newnick", "name": "newname"}
        s = AdminAccountUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

        user = s.save()
        user.refresh_from_db()
        self.assertEqual(user.nickname, "newnick")
        self.assertEqual(user.name, "newname")

    def test_update_invalid_gender_example(self) -> None:
        payload = {"gender": "X"}
        s = AdminAccountUpdateSerializer(instance=self.user, data=payload, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("gender", s.errors)


class AdminAccountResponseSerializerTests(TestCase):
    user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="r@test.com",
            password="pass1234!!",
            nickname="nick",
            name="name",
            phone_number="01099998888",
            birthday=date(1999, 12, 31),
            gender="F",
        )

    def test_response_serializer_fields(self) -> None:
        s = AdminAccountResponseSerializer(instance=self.user)
        self.assertEqual(
            set(s.data.keys()),
            {
                "id",
                "email",
                "nickname",
                "name",
                "phone_number",
                "birthday",
                "gender",
                "status",
                "profile_image_url",
                "updated_at",
            },
        )

    def test_response_values(self) -> None:
        data = AdminAccountResponseSerializer(instance=self.user).data
        expected = "active" if self.user.is_active else "inactive"
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["nickname"], self.user.nickname)
        self.assertEqual(data["name"], self.user.name)
        self.assertEqual(data["status"], expected)


class AdminAccountRoleUpdateSerializerTests(TestCase):
    user: ClassVar[User]

    def test_user_role_only_ok(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "U"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["role"], "U")

    def test_user_role_rejects_extra_fields(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "AD", "cohort_id": 1})
        self.assertFalse(s.is_valid())
        self.assertEqual(str(s.errors["detail"][0]), "USER/ADMIN은 role만 변경 가능합니다.")
        self.assertEqual([str(x) for x in s.errors["allowed_fields"]], ["role"])

        s2 = AdminAccountRoleUpdateSerializer(data={"role": "U", "assigned_courses": [1, 2]})
        self.assertFalse(s2.is_valid())
        self.assertEqual(str(s2.errors["detail"][0]), "USER/ADMIN은 role만 변경 가능합니다.")
        self.assertEqual([str(x) for x in s2.errors["allowed_fields"]], ["role"])

    def test_cohort_role_requires_cohort_id(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "TA"})
        self.assertFalse(s.is_valid())
        self.assertEqual([str(x) for x in s.errors["cohort_id"]], ["학생/조교 권한으로 변경 시 필수 필드입니다."])

        s2 = AdminAccountRoleUpdateSerializer(data={"role": "ST", "cohort_id": None})
        self.assertFalse(s2.is_valid())
        self.assertEqual([str(x) for x in s2.errors["cohort_id"]], ["학생/조교 권한으로 변경 시 필수 필드입니다."])

    def test_cohort_role_rejects_assigned_courses(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "TA", "cohort_id": 3, "assigned_courses": [1]})
        self.assertFalse(s.is_valid())
        self.assertEqual(
            [str(x) for x in s.errors["assigned_courses"]], ["학생/조교 권한으로 변경할 수 없는 필드입니다."]
        )

    def test_cohort_role_ok(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "ST", "cohort_id": 10})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["role"], "ST")
        self.assertEqual(s.validated_data["cohort_id"], 10)

    def test_course_role_requires_assigned_courses(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "OM"})
        self.assertFalse(s.is_valid())
        self.assertEqual(
            [str(x) for x in s.errors["assigned_courses"]],
            ["러닝코치/운영매니저 권한으로 변경 시 필수 필드입니다."],
        )

    def test_course_role_rejects_cohort_id(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "LC", "assigned_courses": [1], "cohort_id": 1})
        self.assertFalse(s.is_valid())
        self.assertEqual(
            [str(x) for x in s.errors["cohort_id"]],
            ["러닝코치/운영매니저 권한으로 변경할 수 없는 필드입니다."],
        )

    def test_course_role_disallows_empty_list_at_field_level(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "OM", "assigned_courses": []})
        self.assertFalse(s.is_valid())
        self.assertIn("assigned_courses", s.errors)

    def test_course_role_ok(self) -> None:
        s = AdminAccountRoleUpdateSerializer(data={"role": "LC", "assigned_courses": [10, 20]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["role"], "LC")
        self.assertEqual(s.validated_data["assigned_courses"], [10, 20])
