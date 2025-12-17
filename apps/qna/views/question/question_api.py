from rest_framework import status
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


class QuestionAPIView(APIView):
    authentication_classes = []

    def get_permissions(self):
        # GET: 모두 허용
        if self.request.method == "GET":
            return []

        # POST: 질문 등록 권한
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
                "results": QuestionListSerializer(questions, many=True).data,
                "page": page_info,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        self.validation_error_message = "유효하지 않은 질문 등록 요청입니다."

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = get_category_or_raise(serializer.validated_data["category"])

        question = create_question(
            author=request.user,
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
