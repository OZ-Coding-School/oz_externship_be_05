import datetime
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions.exception_messages import EMS
from apps.courses.models import Course, Subject
from apps.exams.models import Exam
from apps.exams.services.admin import AdminExamService

# 서비스 인스턴스 생성
exam_service = AdminExamService()


class ExamAdminViewTest(APITestCase):
    """ExamAdminViewSet에 대한 테스트 케이스"""

    # ClassVar로 클래스 속성 선언 (setUpTestData)
    course: ClassVar[Course]
    # admin_user: ClassVar[User]
    admin_user: ClassVar[Any]
    subject_python: ClassVar[Subject]
    subject_flask: ClassVar[Subject]
    subject_django: ClassVar[Subject]

    # 인스턴스 변수 (setUp)
    exam_a: Exam
    exam_b: Exam
    exam_c: Exam

    @classmethod
    def setUpTestData(cls) -> None:
        """
        테스트 전체에서 사용될 공통 데이터 설정
        Read-Only 공통 데이터 (코스, 유저, 과목)
        """
        cls.course = Course.objects.create(name="be 코스")
        cls.admin_user = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="testpassword",
            name="admin",
            birthday=datetime.date(1990, 1, 1),
        )  # 관리자 유저 생성
        cls.subject_python = Subject.objects.create(
            title="Python", course=cls.course, number_of_days=10, number_of_hours=10
        )
        cls.subject_django = Subject.objects.create(
            title="Django", course=cls.course, number_of_days=20, number_of_hours=40
        )
        cls.subject_flask = Subject.objects.create(
            title="Flask", course=cls.course, number_of_days=15, number_of_hours=30
        )

    def setUp(self) -> None:
        """
        각 테스트 메서드 실행 직전 실행됩니다.
        각 테스트마다 새로 생성됩니다.
        """
        self.client.force_authenticate(user=self.admin_user)
        # 수정/삭제 테스트가 섞여있으므로 매번 새로 생성
        # created_at 시간 순서: exam_a < exam_b < exam_c (asc)
        self.exam_a = Exam.objects.create(title="a기초 파이썬 시험", subject=self.subject_python)
        self.exam_b = Exam.objects.create(title="c심화 장고 시험", subject=self.subject_django)
        self.exam_c = Exam.objects.create(title="c심화 플라스크 시험", subject=self.subject_flask)

        self.base_url = reverse("exam")
        self.detail_url = reverse("exam-detail", kwargs={"pk": self.exam_a.pk})

    # --------------------------------------------------------------------
    # 기존 목록 조회 (list) 및 CRUD 테스트
    # --------------------------------------------------------------------

    def test_list_all_exams_and_serializer_check(self) -> None:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        first_result = response.data["results"][0]
        self.assertIn("question_count", first_result)
        self.assertIn("submit_count", first_result)
        self.assertNotIn("thumbnail_img_url", first_result)
        self.assertEqual(first_result["title"], "c심화 플라스크 시험")

    def test_list_exams_with_search_filter(self) -> None:
        response = self.client.get(self.base_url, {"search_keyword": "파이썬"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "a기초 파이썬 시험")

    def test_list_exams_with_subject_id_filter(self) -> None:
        response = self.client.get(self.base_url, {"subject_id": self.subject_django.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "c심화 장고 시험")

    def test_list_exams_with_sorting_created_at_desc(self) -> None:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "c심화 플라스크 시험")

    def test_list_exams_with_sorting_asc(self) -> None:
        response = self.client.get(self.base_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "a기초 파이썬 시험")

    def test_retrieve_exam_without_list_queryset_optimization(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_exam_success_and_serializer_check(self) -> None:
        data = {
            "subject_id": self.subject_python.id,
            "title": "새로 만든 시험",
            "thumbnail_img_url": "http://new.img/url.png",
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exam.objects.count(), 4)
        response_data = response.data
        self.assertIn("thumbnail_img_url", response_data)
        self.assertIn("subject_name", response_data)
        self.assertNotIn("question_count", response_data)

    def test_update_exam_success(self) -> None:
        data = {
            "subject_id": self.subject_django.id,
            "title": "수정된 시험 제목",
            "thumbnail_img_url": "http://updated.img/url.png",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exam_a.refresh_from_db()
        self.assertEqual(self.exam_a.title, "수정된 시험 제목")

    @patch.object(AdminExamService, "update_exam")
    def test_update_exam_not_found_returns_404(self, mock_update_exam: MagicMock) -> None:
        mock_update_exam.side_effect = Exam.DoesNotExist("Exam not found for update")
        data = {"subject_id": self.subject_python.id, "title": "오류 테스트"}
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], EMS.E404_NOT_FOUND("수정할 쪽지시험 정보").get("error_detail"))

    def test_destroy_exam_success(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Exam.objects.count(), 2)

    @patch.object(AdminExamService, "delete_exam")
    def test_destroy_exam_not_found_returns_404(self, mock_delete_exam: MagicMock) -> None:
        # ValueError 대신 Exam.DoesNotExist로 변경
        mock_delete_exam.side_effect = Exam.DoesNotExist
        non_existent_url = reverse("exam-detail", kwargs={"pk": 9999})
        response = self.client.delete(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], EMS.E404_NOT_FOUND("삭제할 쪽지시험 정보").get("error_detail"))

    def test_list_exams_with_search_and_subject_filter(self) -> None:
        """키워드(search_keyword)와 subject_id 필터링 조합 확인"""
        response = self.client.get(self.base_url, {"search_keyword": "시험", "subject_id": str(self.subject_python.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "a기초 파이썬 시험")

    def test_list_exams_with_invalid_subject_id_format(self) -> None:
        """subject_id가 숫자가 아닐 때 필터링 건너뛰는지 확인"""
        response = self.client.get(self.base_url, {"subject_id": "invalid_id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_exams_with_invalid_sort_field(self) -> None:
        """유효하지 않은 정렬 필드 사용 시 기본 정렬(created_at desc) 확인"""
        response = self.client.get(self.base_url, {"sort": "non_existent_field", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["title"], "c심화 플라스크 시험")

    def test_retrieve_non_existent_exam_returns_404(self) -> None:
        """존재하지 않는 ID 조회 시 404 확인"""
        url = reverse("exam-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], EMS.E404_NOT_FOUND("수정할 쪽지시험 정보").get("error_detail"))

    def test_create_exam_with_invalid_subject_id_returns_404(self) -> None:
        """POST 시 유효하지 않은 subject_id (404) 테스트"""
        data = {
            "subject_id": 8888,  # 존재하지 않는 과목
            "title": "에러 테스트",
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], EMS.E404_NOT_FOUND("해당 과목 정보").get("error_detail"))

    def test_create_exam_invalid_serializer_data(self) -> None:
        """필수 필드 누락 등 시리얼라이저 에러 시 400 반환 확인"""
        data = {"title": ""}  # subject_id 누락 및 제목 빈값
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_exam_with_invalid_subject_returns_404(self) -> None:
        """수정 시 존재하지 않는 subject_id를 넣었을 때 404 확인"""
        data = {
            "subject_id": 99999,
            "title": "제목 수정",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], EMS.E404_NOT_FOUND("해당 과목 정보").get("error_detail"))

    @patch.object(AdminExamService, "apply_filters_and_sorting")
    def test_list_exams_value_error_returns_400(self, mock_filter: MagicMock) -> None:
        """목록 조회 시 ValueError 발생 시 400 반환 확인"""
        mock_filter.side_effect = ValueError("Invalid sorting or filter")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], EMS.E400_INVALID_REQUEST("조회").get("error_detail"))

    def test_retrieve_exam_invalid_pk_format(self) -> None:
        """상세 조회 시 PK가 숫자가 아닌 경우 400 반환 확인 (ValueError 대응)"""
        # 이 테스트는 url 패턴이 <int:pk>라면 404가 먼저 뜨겠지만,
        # 뷰의 get_object_for_detail에서 ValueError를 직접 raise 하므로
        # 서비스에서 raise하도록 모킹하거나 경로를 우회해서 체크할 수 있습니다.
        with patch.object(AdminExamService, "get_exam_questions_by_id", side_effect=ValueError):
            response = self.client.get(self.detail_url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_exam_serializer_validation_fail(self) -> None:
        """시리얼라이저 검증 실패 시 400 반환 확인 (커스텀 메시지 블록 검증)"""
        # 필수 필드인 title을 누락하거나 빈 값으로 전송
        data = {"subject_id": self.subject_python.id, "title": ""}
        response = self.client.post(self.base_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 뷰의 except Exception as e 블록 내 EMS.E400_INVALID_REQUEST 확인
        self.assertEqual(response.data["error_detail"], EMS.E400_INVALID_REQUEST("시험 생성").get("error_detail"))

    @patch.object(AdminExamService, "update_exam")
    def test_update_exam_generic_exception_handling(self, mock_update: MagicMock) -> None:
        """수정 시 예상치 못한 에러 발생 시 뷰의 예외 처리 확인"""
        # 에러 객체에 detail 속성이 있는 경우 (DRF 스타일 에러)
        mock_error: Any = Exception("Unexpected Error")
        mock_error.detail = {"field": ["error"]}
        mock_update.side_effect = mock_error

        data = {"subject_id": self.subject_python.id, "title": "에러 테스트"}
        response = self.client.put(self.detail_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], EMS.E400_INVALID_DATA("요청").get("error_detail"))

    def test_list_exams_pagination_check(self) -> None:
        """커스텀 페이지네이션 작동 확인 (size 파라미터 등)"""
        response = self.client.get(self.base_url, {"size": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 한 페이지에 1개만 나오는지 확인
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("next", response.data)  # 다음 페이지 링크 존재 여부
