from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.qna.permissions.question.question_update_permission import (
    QuestionUpdatePermission,
)
from apps.qna.serializers.question.question_detail import QuestionDetailSerializer
from apps.qna.serializers.question.question_update import QuestionUpdateSerializer
from apps.qna.services.question.question_detail.service import get_question_detail
from apps.qna.models.question.question_ai_answer import QuestionAIAnswer
from apps.qna.serializers.question.question_ai_answer_serializer import QuestionAIAnswerSerializer
from apps.qna.services.question.question_update.selectors import get_question_for_update
from apps.qna.services.question.question_update.service import update_question


class QuestionDetailAPIView(APIView):

    def get_authenticators(self) -> list[BaseAuthentication]:
        request = getattr(self, "request", None)
        if request and request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "PATCH":
            return [QuestionUpdatePermission()]
        return []

    @extend_schema(
        tags=["질의응답"],
        summary="질문 상세 조회 API",
        responses=QuestionDetailSerializer,
    )
    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 상세 조회")["error_detail"]

        question = get_question_detail(question_id=question_id)

        return Response(
            QuestionDetailSerializer(
                question,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["질의응답"],
        summary="질문 수정 API",
        request=QuestionUpdateSerializer,
        responses=QuestionDetailSerializer,
    )
    def patch(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("질문 수정")["error_detail"]
        question = get_question_for_update(question_id=question_id)  # 존재 확인

        self.check_object_permissions(request, question)  # 작성자와 사용자가 같은 사람인가 확인

        serializer = QuestionUpdateSerializer(
            instance=question,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        question = update_question(
            question=question,
            validated_data=serializer.validated_data,
        )

        return Response(
            QuestionDetailSerializer(
                question,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )

"""
질문 시 최초 AI답변, 조회 API

"""
class QuestionAIAnswerAPIView(APIView):
    def get_authenticators(self) -> list[BaseAuthentication]:
        request = getattr(self, "request", None)
        if request and request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self) -> list[BasePermission]:
        return []

    @extend_schema(
        tags=["질의응답"],
        summary="AI 답변 생성",
        description=
        "질문 작성 후, 해당 질문에 대해 GET 요청 시 AI 최초 답변을 생성/저장하고 반환합니다.\n"
        "- 동일한 question + using_model 조합의 답변이 이미 존재하면 저장된 답변을 그대로 반환합니다.\n"
        "- 답변이 없으면 새로 생성하여 저장한 뒤 반환합니다.\n"
        "- 응답의 `question` 필드는 질문의 PK(= question_id 의미)입니다.",
        parameters=[
            OpenApiParameter(
                name="using_model",
                type=OpenApiTypes.STR,
                location="query",
                required=False,
                description="사용할 모델 이름. 미입력 시 기본값(gemini-2.5-flash 사용.",
                default="gemini-2.5-flash"
            )
        ],
        responses={
            201: OpenApiResponse(QuestionAIAnswerSerializer,
                                 description="AI 답변이 새로 생성되어 저장된 경우",
                                 examples=[
                                     OpenApiExample(
                                         name="created",
                                         summary="최초 생성",
                                         value={
                                             "id": 123,
                                             "question": 456,
                                             "output": "질문에 대한 AI 최초 답변 내용이 들어갑니다.",
                                             "using_model": "gemini-2.5-flash",
                                             "created_at": "2026-01-04T10:12:34+09:00",}
                                     )
                                 ]
                                 ),
            400: OpenApiResponse(EMS.E400_INVALID_REQUEST("데이터"),
                                 description="요청 파라미터/검증 오류",
                                 examples=[OpenApiExample(
                                     name="invalid_using_model",
                                     summary="using_model 검증 실패(지원하지 않는 모델)",
                                     value={
                                         "success": False,
                                         "code": "E400_INVALID_REQUEST",
                                         "message": "데이터가 올바르지 않습니다.",
                                         "data": {"using_model": ["지원하지 않는 모델입니다."]},},),
                                     OpenApiExample(
                                         name="invalid_query",
                                         summary="쿼리 파라미터 형식 오류",
                                         value={
                                             "success": False,
                                             "code": "E400_INVALID_REQUEST",
                                             "message": "데이터가 올바르지 않습니다.",
                                             "data": {"detail": "Query parameter parsing failed."},},)
                                 ],
                                 ),
            401: OpenApiResponse(EMS.E401_NO_AUTH_DATA,
                                 description="인증 필요",
                                 examples=[OpenApiExample(
                                     name="인증 실패",
                                     summary="로그인 이슈로 인하여 header에 올바르지 않은 토큰값이 들어간 경우",
                                     value={
                                         "error_detail": "자격 인증 데이터가 제공되지 않았습니다."
                                     }
                                 )]),
            403: OpenApiResponse(EMS.E403_PERMISSION_DENIED("AI 답변 생성"),
                                 description="권한 없음",
                                 examples=[OpenApiExample(
                                     name="권한 없음",
                                     summary="해당 유저가 작성한 질문이 아니면 AI답변이 생성되지 않음.",
                                     value={
                                         "error_detail": "AI 답변 생성 권한이 없습니다."
                                     },
                                 )]),
            404: OpenApiResponse(EMS.E404_NOT_EXIST("질문"),
                                 description="질문을 찾을 수 없음",
                                 examples=[OpenApiExample(
                                     name="질문을 찾을 수 없음",
                                     summary="AI답변을 생성하기 위한 질문Question이 존재하지 않음.",
                                     value={
                                         "error_detail": "등록된 질문이(가) 없습니다."
                                     },
                                 )]),
            409: OpenApiResponse(EMS.E409_AI_ALREADY_RESPONDED,
                                 description="동일 질문/모델로 생성 충돌(중복 생성) 또는 생성 중 충돌",
                                 examples=[OpenApiExample(
                                     name="already_responded",
                                     summary="이미 동일 모델로 AI 답변이 존재함",
                                     value={
                                         "success": False,
                                         "code": "E409_AI_ALREADY_RESPONDED",
                                         "message": "이미 AI 답변이 존재합니다.",
                                         "data": {
                                             "question": 456,
                                             "using_model": "gemini-2.5-flash",
                                         },}
                                 )]),
        },
        examples=[
            OpenApiExample(
                name="기본 모델로 생성",
                summary="using_model 생략",
                description="Query parameter 생략하면 기본값(gemini-2.5-flash)을 사용합니다.\n"
                "예) GET /questions/{question}/ai-answer/",
                value={},
                request_only=True,
            ),
            OpenApiExample(
                name="모델 지정하여 생성",
                summary="using_model 지정",
                description="using_model을 쿼리로 전달합니다.\n"
                "예) get /questions/{question}/ai-answer/?using_model=gemini-2.5-flash",
                value={"using_model": "gemini-2.5-flash"},
                request_only=True,
            )
        ],
    )
    def get(self, request: Request, question_id: int) -> Response:
        self.validation_error_message = EMS.E400_INVALID_REQUEST("AI 최초답변 조회")["error_detail"]

        question = get_question_detail(question_id=question_id)

        raw_model = request.query_params.get("using_model")

        from apps.qna.utils.ai_answer_tasks import generate_ai_answer_task, resolve_using_model

        resolved_model = resolve_using_model(raw_model)

        from apps.chatbot.models.chatbot_sessions import ChatModel

        valid_models = {choice[0] for choice in ChatModel.choices}
        if resolved_model not in valid_models:
            return Response(
                {"message": "지원하지 않는 using_model 입니다.", "using_model": resolved_model},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_answer = (
            QuestionAIAnswer.objects.filter(
                question=question,
                using_model=resolved_model,
            )
            .order_by("-created_at")
            .first()
        )
        if ai_answer:
            return Response(QuestionAIAnswerSerializer(ai_answer).data, status=status.HTTP_200_OK)

        generate_ai_answer_task.delay(question.id, resolved_model)
        return Response(
            {
                "message": "AI 답변 생성 중입니다. 잠시 후 다시 조회해주세요.",
                "question": question.id,
                "using_model": resolved_model,
            },
            status=status.HTTP_202_ACCEPTED,
        )