from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.questions.models import Question, QuestionCategory
from apps.questions.serializers import QuestionCreateSerializer
from apps.user.models import RoleChoices, User


class QuestionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        assert isinstance(request.user, User)

        if request.user.role != RoleChoices.ST:
            return Response(
                {"error_detail": "질문 등록 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        title = request.data.get("title")
        if title and Question.objects.filter(title=title).exists():
            return Response(
                {"error_detail": "중복된 질문 제목이 이미 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )

        category_id = request.data.get("category")
        if category_id and not QuestionCategory.objects.filter(id=category_id).exists():
            return Response(
                {"error_detail": "선택한 카테고리를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = QuestionCreateSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            question = serializer.save()
            return Response(
                {
                    "message": "질문이 성공적으로 등록되었습니다.",
                    "question_id": question.id,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error_detail": "유효하지 않은 질문 등록 요청입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )
