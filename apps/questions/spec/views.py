from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import QuestionCreateSpecSerializer


class QuestionCreateSpecAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = QuestionCreateSpecSerializer

    @extend_schema(
        tags=["Questions"],
        summary="질문 등록 API (Spec)",
        description="실제 저장 없이 mock 데이터로 동작하는 질문 등록 Spec API입니다.",
        request=QuestionCreateSpecSerializer,
        responses={
            201: QuestionCreateSpecSerializer,
            400: {"object": "object", "example": {"error": "Bad Request"}},
        },
    )
    def post(self, request: Request) -> Response:

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        mock_response = {
            "id": 1,
            "title": validated["title"],
            "content": validated["content"],
            "category": validated["category"],
            "image_urls": validated.get("image_urls", []),
            "images": [{"img_url": url} for url in validated.get("image_urls", [])],
            "created_at": datetime.now().isoformat(),
        }

        response_serializer = self.serializer_class(mock_response) # type: ignore[arg-type]


        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
