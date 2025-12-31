from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import Exam
from apps.exams.permissions.admin_permission import AdminUserPermissionView
from apps.exams.serializers.admin.admin_exam_serializer import (
    AdminExamListSerializer,
    AdminExamQuestionsListSerializer,
    AdminExamSerializer,
)
from apps.exams.services.admin import AdminExamService

# 서비스 인스턴스 생성
exam_service = AdminExamService()


class ExamCustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "size"
    page_size = 10
    max_page_size = 100


# --------------------------------------------------------------------------
# 쪽지시험 List 및 Create APIView
# --------------------------------------------------------------------------


def get_base_queryset() -> QuerySet[Exam]:
    """기본 쿼리셋을 반환합니다."""
    return exam_service.get_exam_list()


class ExamAdminListCreateAPIView(AdminUserPermissionView):
    """
    쪽지시험(Exam) 엔티티에 대한 관리자 list APIView입니다.
    GET: 쪽지시험 목록 조회
    POST: 쪽지시험 생성
    """

    pagination_class = ExamCustomPageNumberPagination
    serializer_class = AdminExamSerializer  # 기본 시리얼라이저 - POST, PUT, GET 상세용

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 목록 조회",
        description="검색어, 과목 ID, 정렬 기능을 포함한 목록 조회 API입니다.",
        parameters=[
            OpenApiParameter(
                name="search_keyword", description="시험 제목 검색어", required=False, type=OpenApiTypes.STR
            ),
            OpenApiParameter(name="subject_id", description="과목 ID 필터", required=False, type=OpenApiTypes.INT),
            OpenApiParameter(
                name="sort",
                description="정렬 필드 (예: created_at, title)",
                required=False,
                type=OpenApiTypes.STR,
                default="created_at",
            ),
            OpenApiParameter(
                name="order", description="정렬 순서 (asc, desc)", required=False, type=OpenApiTypes.STR, default="desc"
            ),
            # 페이지네이션 파라미터도 필요한 경우 추가
            OpenApiParameter(name="page", description="페이지 번호", required=False, type=OpenApiTypes.INT, default=1),
            OpenApiParameter(
                name="size", description="페이지당 개수", required=False, type=OpenApiTypes.INT, default=10
            ),
        ],
        responses={200: AdminExamListSerializer(many=True)},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        GET: 시험 목록 조회 view
        """
        try:
            queryset = get_base_queryset().select_related("subject")  # annotate가 적용된 쿼리셋을 가져옴
            # 필터링 및 정렬 적용
            queryset = exam_service.apply_filters_and_sorting(queryset, request.query_params)

            # 페이징
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, view=self)

            # 목록 조회: ExamListSerializer
            serializer = AdminExamListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        except ValueError:
            # 유효하지 않은 쿼리 파라미터 (list 400)
            return Response(EMS.E400_INVALID_REQUEST("조회"), status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 생성",
        description="새로운 쪽지시험을 생성합니다. 과목 ID, 시험 제목, 썸네일 URL을 입력받습니다.",
        request=AdminExamSerializer,  # 요청 시 사용할 시리얼라이저
        responses={
            201: AdminExamSerializer,  # 성공 시 생성된 데이터 반환
            400: OpenApiResponse(description="유효하지 않은 입력 데이터"),
            404: OpenApiResponse(description="해당 과목 정보를 찾을 수 없음"),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST: 시험 생성 view (create)"""
        serializer = AdminExamSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)  # 시리얼라이저로 유효성 검사
            exam = exam_service.create_exam(serializer.validated_data)  # 서비스 호출
        except ObjectDoesNotExist:
            return Response(EMS.E404_NOT_FOUND("해당 과목 정보"), status=status.HTTP_404_NOT_FOUND)  # subject_id
        except IntegrityError:
            return Response(EMS.E409_DUPLICATE_NAME("시험"), status=status.HTTP_409_CONFLICT)
        except Exception as e:
            # 시리얼라이저 is_valid(raise_exception=True)에서 발생된 Validation Error는
            # DRF에서 자동으로 400을 반환하지만, 커스텀 메시지를 위해 예외를 잡아서 재처리
            if hasattr(e, "detail") and isinstance(e.detail, dict):
                return Response(EMS.E400_INVALID_REQUEST("시험 생성"), status=status.HTTP_400_BAD_REQUEST)
            raise

        # subject_name N+1 쿼리 방지.
        exam_with_subject = exam_service.get_exam_by_id(exam.pk)
        response_serializer = AdminExamSerializer(exam_with_subject)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ExamAdminRetrieveUpdateDestroyAPIView(AdminUserPermissionView):
    """
    GET: 쪽지시험 상세 조회
    PUT: 쪽지시험 수정
    DELETE: 쪽지시험 삭제
    """

    serializer_class = AdminExamSerializer  # 기본 시리얼라이저 - POST, PUT, GET 상세용

    def get_object_for_detail(self, pk: int) -> Exam:
        """
        PK를 사용하여 Exam 객체를 가져옵니다.
        subject_id의 title을 가져옵니다.
        """
        try:
            return exam_service.get_exam_by_id(pk)
        except ValueError:
            raise ValueError  # PK 포맷 오류 (호출단에 메시지 존재)
        except Exam.DoesNotExist:
            raise Exam.DoesNotExist  # 객체 미발견

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 상세 조회",
        description="특정 ID의 쪽지시험 상세 정보와 속한 문제를 조회합니다.",
        responses={200: AdminExamQuestionsListSerializer},
    )
    def get(self, request: Request, pk: int, *args: Any, **kwargs: Any) -> Response:
        """GET: 시험 상세 조회 view (retrieve)"""
        try:
            exam = exam_service.get_exam_questions_by_id(pk)

            serializer = AdminExamQuestionsListSerializer(exam)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(EMS.E400_INVALID_DATA("요청"), status=status.HTTP_400_BAD_REQUEST)
        except Exam.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("수정할 쪽지시험 정보"), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 수정",
        description="시험 제목, 과목 ID, 썸네일 등을 수정합니다.",
        request=AdminExamSerializer,
        responses={
            200: AdminExamSerializer,
            400: OpenApiResponse(description="유효하지 않은 요청 데이터입니다."),
            404: OpenApiResponse(description="수정할 쪽지시험 정보을(를) 찾을 수 없습니다."),
        },
    )
    def put(self, request: Request, pk: int, *args: Any, **kwargs: Any) -> Response:
        """PUT: 시험 수정 view (update)"""
        try:
            instance = self.get_object_for_detail(pk)

            serializer = self.serializer_class(instance, data=request.data, partial=kwargs.get("partial", False))
            serializer.is_valid(raise_exception=True)
            updated_exam: Exam = exam_service.update_exam(instance, serializer.validated_data)

            response_serializer = self.serializer_class(updated_exam)
            return Response(response_serializer.data)
        except ValueError:
            return Response(EMS.E400_INVALID_DATA("요청"), status=status.HTTP_400_BAD_REQUEST)
        except Exam.DoesNotExist:
            # get_object_for_detail 또는 update_exam 내부에서 발생
            return Response(EMS.E404_NOT_FOUND("수정할 쪽지시험 정보"), status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response(EMS.E409_DUPLICATE_NAME("쪽지시험"), status=status.HTTP_409_CONFLICT)
        except ObjectDoesNotExist:  # subject_id 미발견
            return Response(EMS.E404_NOT_FOUND("해당 과목 정보"), status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # 시리얼라이저 Validation Error (400)
            if hasattr(e, "detail") and isinstance(e.detail, dict):
                return Response(EMS.E400_INVALID_DATA("요청"), status=status.HTTP_400_BAD_REQUEST)
            raise

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 삭제",
        description="특정 쪽지시험을 삭제합니다. 관련 배포 정보 및 제출 내역에 영향을 줄 수 있습니다.",
        responses={
            204: None,
            404: OpenApiResponse(description="삭제할 쪽지시험 정보을(를) 찾을 수 없습니다."),
        },
    )
    def delete(self, request: Request, pk: int, *args: Any, **kwargs: Any) -> Response:
        """DELETE: 시험 삭제 view (destroy)"""
        try:
            exam_service.delete_exam(pk)
        except ValueError:
            return Response(EMS.E400_INVALID_DATA("요청"), status=status.HTTP_400_BAD_REQUEST)
        except Exam.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("삭제할 쪽지시험 정보"), status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
