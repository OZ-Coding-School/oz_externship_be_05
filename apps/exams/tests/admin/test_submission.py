from __future__ import annotations

from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment, ExamSubmission
from apps.user.models import User
from apps.user.models.user import RoleChoices


class AdminExamSubmissionTest(APITestCase):
    def setUp(self) -> None:
        open_at = timezone.make_aware(datetime(2025, 3, 1, 9, 0, 0))
        close_at = timezone.make_aware(datetime(2025, 3, 1, 12, 0, 0))
        started_at = timezone.make_aware(datetime(2025, 3, 1, 10, 3, 12))

        self.url = reverse("exam-submission")

        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass1234!",
            name="관리자",
            nickname="adminnick",
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
            is_staff=True,
            role=RoleChoices.AD,
        )

        self.student = User.objects.create_user(
            email="st@test.com",
            password="pass1234!",
            name="한율",
            nickname="한율_회장",
            phone_number="010-1111-2222",
            gender="M",
            birthday="2000-01-01",
            is_staff=False,
            role=RoleChoices.ST,
        )

        # 코스
        self.course = Course.objects.create(
            name="초격차 백엔드 부트캠프",
            tag="TT",
            description="test course description",
        )

        # 과목
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

        # 과목 생성
        self.subject = Subject.objects.create(
            course=self.course,
            title="service subject",
            number_of_days=1,
            number_of_hours=1,
        )

        # 시험 생성
        self.exam = Exam.objects.create(title="service exam", subject=self.subject, thumbnail_img_url="X")

        self.deployment = ExamDeployment.objects.create(
            cohort=self.cohort,
            exam=self.exam,
            duration_time=60,
            access_code="abc123",
            open_at=open_at,
            close_at=close_at,
            questions_snapshot={},
            status="DeploymentStatus.activated",
        )

        self.submission = ExamSubmission.objects.create(
            submitter=self.student,
            deployment=self.deployment,
            started_at=started_at,
            cheating_count=0,
            answers={},
            score=87,
            correct_answer_count=10,
        )

    def test_401_when_not_authenticated(self) -> None:
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_403_when_not_admin(self) -> None:
        self.client.force_authenticate(self.student)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 403)

    def test_200_ok(self) -> None:
        self.client.force_authenticate(self.admin)

        params: dict[str, str] = {
            "page": "1",
            "size": "10",
            "search_keyword": "한율",
            "cohort_id": str(self.cohort.id),
            "exam_id": str(self.exam.id),
            "sort": "score",
            "order": "desc",
        }

        res = self.client.get(self.url, params)
        print(res.status_code, res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["page"], 1)
        self.assertEqual(res.data["size"], 10)
        self.assertEqual(res.data["total_count"], 1)
        self.assertEqual(res.data["submissions"][0]["submission_id"], self.submission.id)
        self.assertEqual(res.data["submissions"][0]["nickname"], "한율_회장")
        self.assertEqual(res.data["submissions"][0]["name"], "한율")

    def test_200_when_empty_result(self) -> None:
        self.client.force_authenticate(self.admin)

        params: dict[str, str] = {"search_keyword": "존재하지않는키워드"}
        res = self.client.get(self.url, params)

        self.assertEqual(res.status_code, 200)

    def test_400_invalid_sort(self) -> None:
        self.client.force_authenticate(self.admin)

        params: dict[str, str] = {"sort": "invalid", "order": "desc"}
        res = self.client.get(self.url, params)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["error_detail"], "유효하지 않은 요청입니다.")

    def test_400_invalid_order(self) -> None:
        self.client.force_authenticate(self.admin)

        params: dict[str, str] = {"sort": "score", "order": "down"}
        res = self.client.get(self.url, params)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["error_detail"], "유효하지 않은 요청입니다.")
