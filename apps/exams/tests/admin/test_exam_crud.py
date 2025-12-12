# from django.test import TestCase
import datetime
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch  # MagicMock 임포트 추가

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, Subject
from apps.exams.models import Exam
from apps.exams.services.admin import ExamService
from apps.user.models import User


class ExamAdminViewTest(APITestCase):
    """ExamAdminViewSet 대한 테스트 케이스"""

    # ClassVar로 클래스 속성 선언
    course: ClassVar[Course]
    admin_user: ClassVar[User]
    subject_python: ClassVar[Subject]
    subject_flask: ClassVar[Subject]
    subject_django: ClassVar[Subject]
    exam_a: ClassVar[Exam]
    exam_b: ClassVar[Exam]
    exam_c: ClassVar[Exam]

    @classmethod
    def setUpTestData(cls) -> None:  # -> None 추가
        """테스트 전체에서 사용될 공통 데이터 설정"""

        cls.course = Course.objects.create(id=1, name="be 코스")
        # 관리자 유저 생성
        try:
            cls.admin_user = User.objects.create_superuser(
                name="admin_test",
                email="admin@test.com",
                password="testpassword",
                birthday=datetime.date(1990, 1, 1),
            )
        except Exception:
            cls.admin_user = User.objects.create(
                name="admin_test",
                is_staff=True,
                is_superuser=True,
                birthday=datetime.date(1990, 1, 1),
            )

        # Subject 인스턴스 생성
        cls.subject_python = Subject.objects.create(
            id=10, title="Python 기초", number_of_days=30, number_of_hours=10, course_id=cls.course.id
        )
        cls.subject_flask = Subject.objects.create(
            id=15, title="Flask 심화", number_of_days=20, number_of_hours=15, course_id=cls.course.id
        )
        cls.subject_django = Subject.objects.create(
            id=20, title="Django 심화", number_of_days=40, number_of_hours=20, course_id=cls.course.id
        )

        # Exam 인스턴스 생성
        cls.exam_a = Exam.objects.create(
            title="a기초 파이썬 시험", subject=cls.subject_python, created_at="2025-01-01T10:00:00Z"
        )
        cls.exam_b = Exam.objects.create(
            title="c심화 장고 시험", subject=cls.subject_django, created_at="2025-01-02T11:00:00Z"
        )
        cls.exam_c = Exam.objects.create(
            title="c심화 플라스크 시험", subject=cls.subject_flask, created_at="2025-01-20T11:00:00Z"
        )

    def setUp(self) -> None:  # -> None 추가
        """각 테스트 메서드 실행 직전 실행"""
        # 관리자 계정으로 강제 인증 (토큰/세션 상관없이 권한 적용)
        self.client.force_authenticate(user=self.admin_user)
        self.base_url = reverse("exam-list")
        self.detail_url = reverse("exam-detail", kwargs={"pk": self.exam_a.pk})

    # ====================================================================
    # 1. 목록 조회 (list) 및 get_queryset 테스트
    # ====================================================================

    def test_list_all_exams_and_serializer_check(self) -> None:  # -> None 추가
        """
        기본 목록 조회 및 ExamListSerializer 사용 확인.
        (get_queryset의 list 액션 분기 및 ExamListSerializer 검증)
        """
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        # ExamListSerializer 사용 여부 검증 (필드 구조 확인)
        first_result = response.data["results"][0]
        self.assertIn("question_count", first_result)  # List 시리얼라이저에만 있는 필드
        self.assertIn("submit_count", first_result)  # List 시리얼라이저에만 있는 필드
        self.assertNotIn("thumbnail_img_url", first_result)  # ExamSerializer에는 있지만 List에는 없는 필드 (가정)

    def test_list_exams_with_search_filter(self) -> None:  # -> None 추가
        """제목 키워드 필터링(title__icontains) 확인"""
        response = self.client.get(self.base_url, {"search_keyword": "파이썬"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["exam_title"], "a기초 파이썬 시험")

    def test_list_exams_with_subject_id_filter(self) -> None:  # -> None 추가
        """subject_id 필터링 확인"""
        response = self.client.get(self.base_url, {"subject_id": self.subject_django.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["exam_title"], "c심화 장고 시험")

    def test_list_exams_with_sorting_created_at_desc(self) -> None:  # -> None 추가
        """기본 정렬 (created_at desc) 확인"""
        response = self.client.get(self.base_url)  # 기본값: sort=created_at, order=desc
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # desc 정렬 시 exam_c, exam_b, exam_a
        self.assertEqual(response.data["results"][0]["exam_title"], "c심화 플라스크 시험")

    def test_list_exams_with_sorting_asc(self) -> None:  # -> None 추가
        """title 필드 오름차순 정렬 확인"""
        response = self.client.get(self.base_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # '기초'가 '심화'보다 먼저 와야 함
        self.assertEqual(response.data["results"][0]["exam_title"], "a기초 파이썬 시험")

    def test_retrieve_exam_without_list_queryset_optimization(self) -> None:  # -> None 추가
        """단일 조회(retrieve) 시 get_queryset의 list 분기를 건너뛰는지 확인"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_exam_success_and_serializer_check(self) -> None:  # -> None 추가
        """
        시험 생성 성공 및 응답 시 ExamSerializer 사용 확인
        """
        data = {
            "subject_id": self.subject_python.id,
            "exam_title": "새로 만든 시험",
            "thumbnail_img_url": "http://new.img/url.png",
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exam.objects.count(), 4)

        # ExamSerializer 사용 여부 검증
        response_data = response.data
        self.assertIn("thumbnail_img_url", response_data)  # ExamSerializer에 있는 필드
        self.assertIn("subject_title", response_data)  # ExamSerializer에 있는 필드
        self.assertNotIn("question_count", response_data)  # ExamListSerializer에는 있지만 여기는 없어야 함 (계산값임)

    def test_update_exam_success(self) -> None:  # -> None 추가
        """
        시험 수정 성공 확인
        """
        data = {
            "subject_id": self.subject_django.id,  # Subject 변경 시도
            "exam_title": "수정된 시험 제목",
            "thumbnail_img_url": "http://updated.img/url.png",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exam_a.refresh_from_db()
        self.assertEqual(self.exam_a.title, "수정된 시험 제목")

    @patch.object(ExamService, "update_exam")
    def test_update_exam_not_found_returns_404(self, mock_update_exam: MagicMock) -> None:  # MagicMock 및 -> None 추가
        """update_exam 서비스에서 ValueError 발생 시 404 응답 확인"""
        mock_update_exam.side_effect = ValueError("Exam not found for update")
        data = {"subject_id": self.subject_python.id, "exam_title": "오류 테스트"}
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Exam not found for update")

    def test_destroy_exam_success(self) -> None:  # -> None 추가
        """
        시험 삭제 성공 확인
        """
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Exam.objects.count(), 2)

    @patch.object(ExamService, "delete_exam")
    def test_destroy_exam_not_found_returns_404(self, mock_delete_exam: MagicMock) -> None:  # MagicMock 및 -> None 추가
        """delete_exam 서비스에서 ValueError 발생 시 404 응답 확인"""
        mock_delete_exam.side_effect = ValueError("Exam not found for delete")
        # 존재하지 않는 PK에 대한 URL 생성
        non_existent_url = reverse("exam-detail", kwargs={"pk": 9999})
        response = self.client.delete(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Exam not found for delete")
