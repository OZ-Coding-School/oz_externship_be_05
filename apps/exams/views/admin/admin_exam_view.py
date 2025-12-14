from typing import Any, Type

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
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


class ExamAdminViewSet(AdminModelViewSet):
    """
    쪽지시험(Exam) 엔티티에 대한 관리자 CRUD API ViewSet입니다.
    """

    http_method_names = ["get", "post", "put", "delete", "head", "options", "trace"]

    queryset = exam_service.get_exam_list()
    serializer_class: Type[BaseSerializer[Any]] = ExamSerializer  # 기본 시리얼라이저 - POST, PUT, GET 상세용

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
                    "deployments",  # Exam 모델에 정의된 related_name="deployments" 사용
                    queryset=ExamDeployment.objects.prefetch_related("submissions"),
                )
            )

            # 필터링 서비스단으로 이동 검토.(추후 다른곳에서도 작업시)
            query_params = self.request.query_params

            search_keyword = query_params.get("search_keyword")
            subject_id = query_params.get("subject_id")
            sort_field = query_params.get("sort")
            order = query_params.get("order", "desc")  # default 내림차순

            # 키워드 필터
            if search_keyword:
                queryset = queryset.filter(
                    title__icontains=search_keyword
                )  # Exam 모델의 대소문자무시(i) search_keyword포함 제목 필터링
            # 과정 필터
            if subject_id and subject_id.isdigit():
                queryset = queryset.filter(subject_id=subject_id)

            # 명시되지 않은 필터 요청 Default값으로 처리
            if sort_field is None or sort_field not in self.valid_sort_fields:
                sort_field = "created_at"
                order = "desc"

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
        * PUT/PATCH: update(PATCH 막음)
        * DELETE: destroy
        """
        if self.action == "list":
            return ExamListSerializer

        # POST, PUT, DELETE, GET 상세 조회
        return self.serializer_class

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        커스텀 예외처리를 위하여 추가된 함수입니다.
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())

            if not queryset.exists():  # 필터링 후 결과가 없을 때
                return Response({"detail": "등록된 쪽지시험이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

            # 3. Pagination 및 응답 생성
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except ValueError:
            return Response({"detail": "유효하지 않은 조회 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """POST: 시험 생성 view"""
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            # 2. 서비스 호출 및 404, 409 처리
            exam = exam_service.create_exam(serializer.validated_data)  # 서비스 호출 및 db저장

        except ObjectDoesNotExist:
            return Response({"detail": "해당 과목 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({"detail": "동일한 이름의 시험이 이미 존재합니다."}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            if hasattr(e, "detail") and isinstance(e.detail, dict):
                return Response({"detail": "유효하지 않은 시험 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
            raise

        exam_with_subject = Exam.objects.select_related("subject").get(pk=exam.pk)  # subject_title N+1 쿼리 방지
        response_serializer = ExamSerializer(exam_with_subject)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """PUT/PATCH: 시험 수정 view"""
        partial = kwargs.pop("partial", False)
        try:
            exam_id_value = self.kwargs.get("pk")

            if exam_id_value is None:  # 필수값 확인
                raise ValueError("Primary key (pk) not provided.")
            exam_id: int = int(exam_id_value)

            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            updated_exam: Exam = exam_service.update_exam(exam_id, serializer.validated_data)
        except ValueError:
            return Response({"detail": "유효하지 않은 요청 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST)
        except Exam.DoesNotExist:
            return Response({"detail": "수정할 쪽지시험 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({"detail": "동일한 이름의 쪽지시험이 이미 존재합니다."}, status=status.HTTP_409_CONFLICT)
        except TypeError:
            return Response({"detail": "유효하지 않은 요청 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST)

        updated_exam_with_subject = Exam.objects.select_related("subject").get(pk=updated_exam.pk)
        response_serializer = ExamSerializer(updated_exam_with_subject)
        return Response(response_serializer.data)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """DELETE: 시험 삭제 view"""
        try:
            exam_id_value = self.kwargs.get("pk")

            if exam_id_value is None:
                raise ValueError("Primary key (pk) not provided.")
            exam_id: int = int(exam_id_value)

            exam_service.delete_exam(exam_id)
        except ValueError:
            return Response({"detail": "유효하지 않은 요청 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST)

        except Exam.DoesNotExist:
            return Response({"detail": "수정할 쪽지시험 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        except TypeError:
            return Response({"detail": "유효하지 않은 요청 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
