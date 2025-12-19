from typing import cast

from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
    get_category_or_raise,
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
        self.validation_error_message = "유효하지 않은 목록 조회 요청입니다."

        query_serializer = QuestionListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        questions, page_info = get_question_list(**query_serializer.validated_data)

        return Response(
            {
                "page": page_info["page"],
                "size": page_info["page_size"],
                "total_count": page_info["total_count"],
                "questions": QuestionListSerializer(questions, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        self.validation_error_message = "유효하지 않은 질문 등록 요청입니다."

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = get_category_or_raise(serializer.validated_data["category_id"])

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
