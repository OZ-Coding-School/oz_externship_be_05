from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.spec.question.spec_question_list.serializers import (
    QuestionListSpecSerializer,
)


class QuestionListSpecAPIView(APIView):
    permission_classes = []

    @extend_schema(
        tags=["Questions"],
        summary="질문 조회 API (Spec)",
        description="실제 저장 없이 mock 데이터로 동작하는 질문 조회 Spec API입니다.",
        request=QuestionListSpecSerializer,
        responses={
            200: QuestionListSpecSerializer,
            400: {"object": "object", "example": {"error_detail": "유효하지 않은 목록 조회 요청입니다."}},
            404: {"object": "object", "example": {"error_detail": "조회 가능한 질문이 존재하지 않습니다."}},
        },
    )
    def get(self, request: Request) -> Response:
        mock_results = [
            {
                "id": 1,
                "category": {
                    "id": 15,
                    "path": "백엔드 > 웹프레임워크 > Django",
                },
                "author": {
                    "nickname": "졸린개발자",
                    "profile_image_url": "https://example.com/profile1.png",
                },
                "title": "Django ORM 질문",
                "content_preview": "Django에서 annotate를 사용하는 방법이 궁금합니다...",
                "answer_count": 1,
                "view_count": 120,
                "thumbnail_image_url": "https://example.com/thumb1.png",
                "created_at": datetime(2025, 12, 13, 9, 0, 0),
            },
            {
                "id": 2,
                "category": {
                    "id": 22,
                    "path": "백엔드 > 데이터베이스 > PostgreSQL",
                },
                "author": {
                    "nickname": "초보개발자",
                    "profile_image_url": None,
                },
                "title": "PostgreSQL 인덱스 질문",
                "content_preview": "인덱스를 언제 사용하는 게 좋은지 궁금합니다...",
                "answer_count": 0,
                "view_count": 45,
                "thumbnail_image_url": None,
                "created_at": datetime(2025, 12, 12, 18, 40, 0),
            },
        ]

        serializer = QuestionListSpecSerializer(mock_results, many=True)

        return Response(
            {
                "count": 2,
                "next": None,
                "previous": None,
                "results": serializer.data,
            }
        )
