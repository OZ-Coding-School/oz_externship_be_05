from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.exceptions.question_exceptions import (
    QuestionCreateValidationError,
)
from apps.qna.permissions.question.question_create_permission import (
    QuestionCreatePermission,
)
from apps.qna.serializers.question.question_create import QuestionCreateSerializer
from apps.qna.services.question.question_create_service import create_question
from apps.user.models import User


class QuestionCreateAPIView(APIView):
    permission_classes = [QuestionCreatePermission]

    def post(self, request: Request) -> Response:
        user = request.user
        assert isinstance(user, User)

        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise QuestionCreateValidationError()

        question = create_question(
            author=user,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            category_id=serializer.validated_data["category"],
            image_urls=serializer.validated_data.get("image_urls", []),
        )

        return Response(
            {
                "message": "질문이 성공적으로 등록되었습니다.",
                "question_id": question.id,
            },
            status=status.HTTP_201_CREATED,
        )
