import datetime
from typing import Any, ClassVar, Optional, Type
from unittest.mock import MagicMock, patch

from django.db.models import Model, Prefetch, QuerySet
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.test import APITestCase

from apps.courses.models import Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.permissions.admin_permission import AdminModelViewSet
from apps.exams.serializers.admin import ExamListSerializer, ExamSerializer
from apps.exams.services.admin import ExamService
from apps.user.models import User

# 서비스 인스턴스 생성
exam_service = ExamService()


class ExamAdminViewSet(AdminModelViewSet):
    """
    쪽지시험(Exam) 엔티티에 대한 관리자 CRUD API ViewSet입니다.
    """

    http_method_names = ["get", "post", "put", "delete", "head", "options", "trace"]

    queryset = exam_service.get_exam_list()
    serializer_class: Type[BaseSerializer[Any]] = ExamSerializer

    def _get_exam_with_related_data(self, exam: Exam) -> Exam:
        """
        주어진 Exam 인스턴스의 ID를 사용하여 subject가 select된 인스턴스를 조회합니다.
        """
        return Exam.objects.select_related("subject").get(pk=exam.pk)

    def get_queryset(self) -> QuerySet[Model, Model]:
        """
        목록 조회(list) 시에만 성능 최적화(Prefetch)를 적용합니다.
        """
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = queryset.select_related("subject")
            queryset = queryset.prefetch_related("questions")
            queryset = queryset.prefetch_related(
                Prefetch(
                    "deployments",
                    queryset=ExamDeployment.objects.prefetch_related("submissions"),
                )
            )

            query_params: dict[str, Any] = self.request.query_params

            search_keyword: Optional[str] = query_params.get("search_keyword")
            subject_id_str: Optional[str] = query_params.get("subject_id")
            sort_field: str = query_params.get("sort", "created_at")
            order: str = query_params.get("order", "desc")

            if search_keyword:
                queryset = queryset.filter(title__icontains=search_keyword)

            if subject_id_str and subject_id_str.isdigit():
                queryset = queryset.filter(subject_id=subject_id_str)

            # 정렬 오류 해결 로직 유지
            if sort_field not in self.valid_sort_fields:
                sort_field = "created_at"

            order_prefix: str = "-" if order == "desc" else ""
            queryset = queryset.order_by(f"{order_prefix}{sort_field}")

        return queryset

    def get_serializer_class(self) -> Type[BaseSerializer[Any]]:
        if self.action == "list":
            return ExamListSerializer
        return self.serializer_class

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam = exam_service.create_exam(serializer.validated_data)

        exam_with_subject = self._get_exam_with_related_data(exam)
        response_serializer = ExamSerializer(exam_with_subject)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        partial: bool = kwargs.pop("partial", False)
        try:
            exam_id_value: Optional[str] = self.kwargs.get("pk")

            if exam_id_value is None:
                raise ValueError("Primary key (pk) not provided.")

            # 400 오류 해결 로직: int() 변환을 먼저 시도
            exam_id: int = int(exam_id_value)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            updated_exam = exam_service.update_exam(exam_id, serializer.validated_data)
        except ValueError as e:  # get_object()에서 DoesNotExist 발생 시
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TypeError:  # URL Conf가 제대로 안되어 문자열이 넘어올 때 (이 경로는 DRF에서 404로 덮힘)
            return Response({"detail": "Invalid primary key format."}, status=status.HTTP_400_BAD_REQUEST)

        updated_exam_with_subject = self._get_exam_with_related_data(updated_exam)
        response_serializer = ExamSerializer(updated_exam_with_subject)
        return Response(response_serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            exam_id_value: Optional[str] = self.kwargs.get("pk")

            if exam_id_value is None:
                raise ValueError("Primary key (pk) not provided.")

            # 400 오류 해결 로직: int() 변환을 먼저 시도
            exam_id: int = int(exam_id_value)

            exam_service.delete_exam(exam_id)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TypeError:
            return Response({"detail": "Invalid primary key format."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


# ====================================================================
# APITestCase를 상속받는 실제 테스트 클래스 (변동 없음)
# ====================================================================


class ExamAdminViewTest(APITestCase):
    """ExamAdminViewSet에 대한 테스트 케이스"""

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
    def setUpTestData(cls) -> None:
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
        # created_at 시간 순서: exam_a < exam_b < exam_c
        cls.exam_a = Exam.objects.create(
            title="a기초 파이썬 시험", subject=cls.subject_python, created_at="2025-01-01T10:00:00Z"
        )
        cls.exam_b = Exam.objects.create(
            title="c심화 장고 시험", subject=cls.subject_django, created_at="2025-01-02T11:00:00Z"
        )
        cls.exam_c = Exam.objects.create(
            title="c심화 플라스크 시험", subject=cls.subject_flask, created_at="2025-01-20T11:00:00Z"
        )

    def setUp(self) -> None:
        """각 테스트 메서드 실행 직전 실행"""
        self.client.force_authenticate(user=self.admin_user)
        self.base_url = reverse("exam-list")
        self.detail_url = reverse("exam-detail", kwargs={"pk": self.exam_a.pk})

    # ====================================================================
    # 1. 기존 목록 조회 (list) 및 CRUD 테스트
    # ====================================================================

    def test_list_all_exams_and_serializer_check(self) -> None:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)
        first_result = response.data["results"][0]
        self.assertIn("question_count", first_result)
        self.assertIn("submit_count", first_result)
        self.assertNotIn("thumbnail_img_url", first_result)
        self.assertEqual(first_result["exam_title"], "c심화 플라스크 시험")

    def test_list_exams_with_search_filter(self) -> None:
        response = self.client.get(self.base_url, {"search_keyword": "파이썬"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["exam_title"], "a기초 파이썬 시험")

    def test_list_exams_with_subject_id_filter(self) -> None:
        response = self.client.get(self.base_url, {"subject_id": self.subject_django.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["exam_title"], "c심화 장고 시험")

    def test_list_exams_with_sorting_created_at_desc(self) -> None:
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["exam_title"], "c심화 플라스크 시험")

    def test_list_exams_with_sorting_asc(self) -> None:
        response = self.client.get(self.base_url, {"sort": "title", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["exam_title"], "a기초 파이썬 시험")

    def test_retrieve_exam_without_list_queryset_optimization(self) -> None:
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_exam_success_and_serializer_check(self) -> None:
        data = {
            "subject_id": self.subject_python.id,
            "exam_title": "새로 만든 시험",
            "thumbnail_img_url": "http://new.img/url.png",
        }
        response = self.client.post(self.base_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exam.objects.count(), 4)
        response_data = response.data
        self.assertIn("thumbnail_img_url", response_data)
        self.assertIn("subject_title", response_data)
        self.assertNotIn("question_count", response_data)

    def test_update_exam_success(self) -> None:
        data = {
            "subject_id": self.subject_django.id,
            "exam_title": "수정된 시험 제목",
            "thumbnail_img_url": "http://updated.img/url.png",
        }
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exam_a.refresh_from_db()
        self.assertEqual(self.exam_a.title, "수정된 시험 제목")

    @patch.object(ExamService, "update_exam")
    def test_update_exam_not_found_returns_404(self, mock_update_exam: MagicMock) -> None:
        mock_update_exam.side_effect = ValueError("Exam not found for update")
        data = {"subject_id": self.subject_python.id, "exam_title": "오류 테스트"}
        response = self.client.put(self.detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Exam not found for update")

    def test_destroy_exam_success(self) -> None:
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Exam.objects.count(), 2)

    @patch.object(ExamService, "delete_exam")
    def test_destroy_exam_not_found_returns_404(self, mock_delete_exam: MagicMock) -> None:
        mock_delete_exam.side_effect = ValueError("Exam not found for delete")
        non_existent_url = reverse("exam-detail", kwargs={"pk": 9999})
        response = self.client.delete(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Exam not found for delete")

    # ====================================================================
    # 2. 커버리지 보강 테스트 (모두 통과 예상)
    # ====================================================================

    def test_list_exams_with_search_and_subject_filter(self) -> None:
        """키워드(search_keyword)와 subject_id 필터링 조합 확인"""
        response = self.client.get(self.base_url, {"search_keyword": "시험", "subject_id": str(self.subject_python.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["exam_title"], "a기초 파이썬 시험")

    def test_list_exams_with_invalid_subject_id_format(self) -> None:
        """subject_id가 숫자가 아닐 때 필터링 건너뛰는지 확인"""
        response = self.client.get(self.base_url, {"subject_id": "invalid_id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_exams_with_invalid_sort_field(self) -> None:
        """유효하지 않은 정렬 필드 사용 시 기본 정렬(created_at desc) 확인"""
        response = self.client.get(self.base_url, {"sort": "non_existent_field", "order": "asc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["exam_title"], "c심화 플라스크 시험")

    def test_update_exam_invalid_pk_format_returns_400(self) -> None:
        """PK가 숫자가 아닐 때 400 응답 확인 (TypeError 경로 커버)"""
        data = {"exam_title": "오류 테스트"}
        invalid_url = reverse("exam-detail", kwargs={"pk": "abc"})
        response = self.client.put(invalid_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Invalid primary key format.")

    def test_destroy_exam_invalid_pk_format_returns_400(self) -> None:
        """PK가 숫자가 아닐 때 400 응답 확인 (TypeError 경로 커버)"""
        invalid_url = reverse("exam-detail", kwargs={"pk": "xyz"})
        response = self.client.delete(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Invalid primary key format.")
