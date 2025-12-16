from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.permissions.question.question_create_permission import (
    QuestionCreatePermission,
)
from apps.qna.serializers.question.question_create import QuestionCreateSerializer
from apps.qna.services.question.question_create_service import (
    create_question,
    get_category_or_raise,
)
from apps.user.models import User


class QuestionCreateAPIView(APIView):
    permission_classes = [QuestionCreatePermission]

    validation_error_message = "유효하지 않은 질문 등록 요청입니다."

    def post(self, request: Request) -> Response:
        user = request.user
        assert isinstance(user, User)

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = get_category_or_raise(serializer.validated_data["category"])

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
