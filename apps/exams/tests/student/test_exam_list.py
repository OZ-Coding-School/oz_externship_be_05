import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject

# 프로젝트 구조에 맞는 임포트 경로 확인 필요
from apps.exams.models import DeploymentStatus, Exam, ExamDeployment, ExamSubmission
from apps.user.models.role import CohortStudent


class ExamListTestCase(APITestCase):
    student_user: Any
    other_user: Any
    course: Course
    subject: Subject
    cohort: Cohort
    exams: list[Exam]
    deployments: list[ExamDeployment]
    submission: ExamSubmission
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        """
        ERD 및 Django 모델 필드명을 완벽히 반영한 데이터 생성
        """
        User = get_user_model()
        now = timezone.now()

        # 1. 유저 생성 (관리자 권한 포함)
        cls.student_user = User.objects.create_superuser(
            email="student@test.com",
            password="testpassword",
            name="한율",
            birthday=datetime.date(2000, 1, 1),
        )
        cls.other_user = User.objects.create_superuser(
            email="other@test.com",
            password="testpassword",
            name="머용",
            birthday=datetime.date(1990, 1, 1),
        )

        # 인프라 데이터(Course, Subject, Cohort) 생성
        cls.course = Course.objects.create(name="백엔드 과정")
        cls.subject = Subject.objects.create(
            course=cls.course, title="파이썬 기초", number_of_days=10, number_of_hours=40
        )
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=14,
            max_student=30,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=90),
        )

        # 3. 유저를 기수에 할당
        CohortStudent.objects.create(user=cls.student_user, cohort=cls.cohort)

        # 시험(Exam) 생성
        cls.exams = [Exam.objects.create(title=f"시험 {i}", subject=cls.subject) for i in range(15)]

        # 시험 배포(ExamDeployment) 생성
        cls.deployments = [
            ExamDeployment.objects.create(
                exam=cls.exams[i],
                cohort=cls.cohort,
                status=DeploymentStatus.ACTIVATED,
                open_at=now - datetime.timedelta(days=1),
                close_at=now + datetime.timedelta(days=7),
                questions_snapshot=[],
                access_code=f"TEST-CODE-{i}",
                duration_time=60,
            )
            for i in range(15)
        ]

        # 제출 기록(ExamSubmission) 생성
        cls.submission = ExamSubmission.objects.create(
            deployment=cls.deployments[0],
            submitter=cls.student_user,
            score=100,
            started_at=now - datetime.timedelta(minutes=30),
            correct_answer_count=10,
            cheating_count=0,
            answers={},
        )

        # URL 설정
        cls.url = reverse("exam_deployment")

    def setUp(self) -> None:
        """매 테스트 케이스 실행 전 학생 유저로 인증"""
        self.client.force_authenticate(user=self.student_user)

    def test_infinite_scroll_pagination(self) -> None:
        """페이지네이션 및 status 파라미터 필수 대응"""
        response = self.client.get(self.url, {"size": "10", "status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 14)  # 전체 15개 중 제출한 1개 제외

    def test_filter_status_done(self) -> None:
        """완료된(done) 시험 필터링 확인"""
        response = self.client.get(self.url, {"status": "done"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.deployments[0].id)

    def test_invalid_status_parameter(self) -> None:
        """잘못된 status 파라미터 시 400 에러 확인"""
        response = self.client.get(self.url, {"status": "wrong_value"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "올바르지 않은 status 파라미터입니다.")

    def test_no_cohort_user_returns_empty_list(self) -> None:
        """기수가 없는 유저는 200 OK와 빈 결과를 반환받음"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url, {"status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_ordering_by_created_at_desc(self) -> None:
        """최신 생성순(ID 역순) 정렬 확인"""
        response = self.client.get(self.url, {"status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 리스트의 첫 번째 항목이 가장 마지막에 생성된 배포여야 함
        self.assertEqual(response.data["results"][0]["id"], self.deployments[-1].id)
