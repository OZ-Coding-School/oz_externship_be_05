from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class QuestionDetailAPIView(APIView):
    authentication_classes = []

    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = "유효하지 않은 질문 상세 조회 요청입니다."

        question = get_question_detail(question_id=question_id)

        return Response(
            QuestionDetailSerializer(question).data,
            status=status.HTTP_200_OK,
        )
