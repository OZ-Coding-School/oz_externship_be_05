from typing import Any, ClassVar, Optional, Type

from django.db.models import Model, Prefetch, QuerySet
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, Serializer

from apps.exams.models import Exam, ExamDeployment
from apps.exams.permissions.admin_permission import AdminModelViewSet
from apps.exams.serializers.admin import ExamListSerializer, ExamSerializer
from apps.exams.services.admin import ExamService

# 서비스 인스턴스 생성
exam_service = ExamService()


# [Exam] 제네릭 타입 추가 (가장 중요한 mypy 오류 해결)
class ExamAdminViewSet(AdminModelViewSet[Exam]):
    """
    쪽지시험(Exam) 엔티티에 대한 관리자 CRUD API ViewSet입니다.
    """

    http_method_names: ClassVar[list[str]] = ["get", "post", "put", "delete", "head", "options", "trace"]  # 타입 추가

    queryset: QuerySet[Exam] = exam_service.get_exam_list()  # 타입 명시
    serializer_class: Type[BaseSerializer[Any]] = ExamSerializer  # 기본 시리얼라이저 - POST, PUT, GET 상세용

    def get_queryset(self) -> QuerySet[Exam]:  # QuerySet[Exam]으로 반환 타입 명시
        """
        목록 조회(list) 시에만 성능 최적화(Prefetch)를 적용합니다.
        """
        queryset: QuerySet[Exam] = super().get_queryset()  # 타입 명시

        if self.action == "list":
            queryset = queryset.select_related("subject")
            queryset = queryset.prefetch_related("questions")
            queryset = queryset.prefetch_related(
                Prefetch(
                    "deployments",  # Exam 모델에 정의된 related_name="deployments" 사용
                    queryset=ExamDeployment.objects.prefetch_related("submissions"),
                )
            )

            # 필터링 서비스단으로 이동 검토.(추후 다른곳에서도 작업시)
            query_params: dict[str, Any] = self.request.query_params

            search_keyword: Optional[str] = query_params.get("search_keyword")
            subject_id_str: Optional[str] = query_params.get("subject_id")
            sort_field: str = query_params.get("sort", "created_at")  # default 만든 시각
            order: str = query_params.get("order", "desc")  # default 내림차순

            # 키워드 필터
            if search_keyword:
                queryset = queryset.filter(
                    title__icontains=search_keyword
                )  # Exam 모델의 대소문자무시(i) search_keyword포함 제목 필터링
            # 과정 필터
            if subject_id_str and subject_id_str.isdigit():
                queryset = queryset.filter(subject_id=subject_id_str)

            if sort_field in self.valid_sort_fields:
                order_prefix: str = "-" if order == "desc" else ""  # desc: -, asc: default
                queryset = queryset.order_by(f"{order_prefix}{sort_field}")

        return queryset

    def get_serializer_class(self) -> Type[BaseSerializer[Any]]:
        """
        요청 액션에 따라 다른 시리얼라이저를 사용합니다.
        get_serializer -> get_serializer_class

        * GET (목록): list
        * GET (상세): retrieve
        * POST: create
        * PUT/PATCH: update
        * DELETE: destroy
        """
        if self.action == "list":
            return ExamListSerializer

        # POST, PUT, DELETE, GET 상세 조회
        return self.serializer_class

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST: 시험 생성 view"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam: Exam = exam_service.create_exam(serializer.validated_data)  # 타입 추가

        exam_with_subject: Exam = Exam.objects.select_related("subject").get(pk=exam.pk)  # subject_title N+1 쿼리 방지
        response_serializer = ExamSerializer(exam_with_subject)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """PUT/PATCH: 시험 수정 view"""
        partial: bool = kwargs.pop("partial", False)  # 타입 추가
        try:
            exam_id_value: Optional[str] = self.kwargs.get("pk")  # 타입 추가

            if exam_id_value is None:
                raise ValueError("Primary key (pk) not provided.")

            exam_id: int = int(exam_id_value)  # int로 변환 (mypy 오류 해결)

            instance: Exam = self.get_object()  # 타입 추가
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            updated_exam: Exam = exam_service.update_exam(exam_id, serializer.validated_data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TypeError:  # int() 변환 실패 시
            return Response({"detail": "Invalid primary key format."}, status=status.HTTP_400_BAD_REQUEST)

        updated_exam_with_subject: Exam = Exam.objects.select_related("subject").get(pk=updated_exam.pk)  # 타입 추가
        response_serializer = ExamSerializer(updated_exam_with_subject)
        return Response(response_serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """DELETE: 시험 삭제 view"""
        try:
            exam_id_value: Optional[str] = self.kwargs.get("pk")  # 타입 추가

            if exam_id_value is None:
                raise ValueError("Primary key (pk) not provided.")

            exam_id: int = int(exam_id_value)  # int로 변환 (mypy 오류 해결)

            exam_service.delete_exam(exam_id)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TypeError:  # int() 변환 실패 시
            return Response({"detail": "Invalid primary key format."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
