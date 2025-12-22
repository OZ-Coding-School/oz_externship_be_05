from typing import cast

from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.pagination import QuestionPageNumberPagination
from apps.qna.permissions.question.question_create_permission import (
    QuestionCreatePermission,
)
from apps.qna.serializers.question.question_create import QuestionCreateSerializer
from apps.qna.serializers.question.question_list import QuestionListSerializer
from apps.qna.serializers.question.question_list_query import (
    QuestionListQuerySerializer,
)
from apps.qna.services.question.question_create_service import (
    create_question,
)
from apps.qna.services.question.question_list.service import get_question_list
from apps.user.models import User


class QuestionAPIView(APIView):

    def get_authenticators(self) -> list[BaseAuthentication]:
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "POST":
            return [QuestionCreatePermission()]
        return []

    def get(self, request: Request) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 목록 조회")["error_detail"]

        # Query 파싱 (엄격 검증 X)
        query_serializer = QuestionListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # QuerySet만 받아옴 (pagination 없음)
        queryset = get_question_list(**query_serializer.validated_data)

        # DRF Pagination 적용
        paginator = QuestionPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)

        # Serializer
        serializer = QuestionListSerializer(page, many=True)

        # DRF 표준 응답
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 등록")["error_detail"]

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = serializer.validated_data["category"]

        user = cast(User, request.user)

        question = create_question(
            author=user,
            category=category,
            validated_data=serializer.validated_data,
        )

        return Response(
            {
                "message": "질문이 성공적으로 등록되었습니다.",
                "question_id": question.id,
            },
            status=status.HTTP_201_CREATED,
        )
