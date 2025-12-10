from random import randint

from drf_spectacular.utils import extend_schema
from requests import session
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.aichatbot.serializers import (
    CompletionCreateSerializer,
    CompletionSerializer,
    SessionCreateSerializer,
    SessionSerializer,
)

from .mock import MockData

"""
세션
POST 세션 생성
GET 세션 목록

세션 상세
GET 세션의 대화내역 목록
DELETE 세션의 대화내역 전체 삭제

메세지 생성
POST prompt 받아 답변 생성 → 수정사항: prompt 칼럼 삭제

스트리밍: 별도 엔드포인트로 분리하고, 일단은 501로 스킵?
"""


class SessionGenerator(APIView):
    serializer_class = SessionCreateSerializer
    permission_classes = [AllowAny]  # IsAuthenticated

    @extend_schema(
        tags=["Session"],
        summary="세션 생성 API (Spec)",
        request=SessionCreateSerializer,
        responses={
            "201": SessionCreateSerializer,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
        },
    )
    # 공부용 주석
    # Serializers는 여기서 request.data(JSON Body)를 받아서 정의된 필드 타입으로 파싱 →
    # is_valid()로 필수존재 여부,타입,길이 검증 → validated_data에서 검증된 값 추출
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        print("test: serializer 통과")

        if serializer.is_valid():
            question = serializer.validated_data.get("question", "")
            title = serializer.validated_data.get("title", "")
            using_model = serializer.validated_data.get("using_model", "")
            print("테스트: question, title 입력 성공")

            new_session = MockData.mock_session_post(question=question, title=title, using_model=using_model)
            print("테스트: new_session에 입력 완료")

            return Response(new_session, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionListView(APIView):
    permission_classes = [AllowAny]  # IsAuthenticated
    serializer_class = SessionSerializer

    @extend_schema(
        tags=["Session"],
        summary="세션 리스트 확인 API (Spec)",
        request=SessionSerializer,
        responses={
            "200": SessionSerializer,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
        },
    )

    # 공부용 주석
    # 이 API에선 입력 데이터 없음 → serializer 필요없...나?
    # extend_schema의 responses에서 응답 스키마 문서화 용도로만 사용.
    # 차후 수정: Serializer(queryset, many=True).data로 직렬화하기
    def get(self, request: Request) -> Response:
        sessions = MockData.mock_session()
        print("test: MockData 조회 성공, 길이: ", len(sessions))

        mock_list: list[dict[str, str | int]] = [
            {
                "id": session["id"],
                "question": session["question"],
                "title": session["title"],
            }
            for session in sessions  # 이거 무슨 문법인지 확인
        ]
        print("테스트: mock list 데이터 넣었나요: ", mock_list[0])
        return Response(mock_list, status=status.HTTP_200_OK)


# 세션 상세.
class SessionDetailView(APIView):
    permission_classes = [AllowAny]  # IsAuthenticated
    serializer_class = SessionSerializer

    @extend_schema(
        tags=["Session Detail"],
        summary="",
        request=SessionSerializer,
        responses={
            "200": SessionSerializer,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
        },
    )

    # 공부용 주석
    # GET상세조회
    # serializers: URL 파라미터로 조회해서 body검증 필요x
    # 실제 구현은 Serializer(instance).data로 직렬화할것
    # 주석 처리 사유: session detail 왜 필요하지? user 입장에선 바로 completions 들어가지 않나?

    # def get(self, request: Request, session_id: int) -> Response:
    #
    #     sessions = MockData.mock_session()
    #     print("test: MockData에서 하나 받아오기 테스트 with len", len(sessions))
    #
    #     session_detail =
    #
    #     session_id = serializer.validated_data.get("session", "")
    #     session_detail = MockData.mock_session(session=session_id)
    #     return Response(session_detail, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Session Detail"],
        summary="",
        request=SessionSerializer,
        responses={
            "204": None,
            "400": {"object": "object", "example": {"error": "Bad Request"}},
            "404": {"object": "object", "example": {"error": "Not Found"}},
        },
    )
    # 나중에 세션 제거기능 구현
    # 실제 구현은 객체 조회 후 .delete() 호출.
    # session = get_object_or_404(ChatbotSession, id=session_id)
    # session.delete()
    def delete(self, request: Request, session_id: int) -> Response:

        # 더미용 데이터. 터미널에서만 출력 예정
        sessions = MockData.mock_session()
        session = sessions[int(session_id)]
        print("테스트: MockData 조회 성공, 인자 갯수(7 정상): ", len(session))
        print(f"테스트: 제목: ", session)
        return Response(status=status.HTTP_204_NO_CONTENT)


# # 세션에 메세지 추가
# class MessageCreateView(APIView):
#     permission_classes = [AllowAny]  # IsAuthenticated
#
#     def post(self, request, session_id: int, *args, **kwargs):
#         pass
#
#
# class StreamingPlaceholderView(APIView):
#     permission_classes = [AllowAny]  # IsAuthenticated
#
#     def get(self, request, *args, **kwargs):
#         # return Response()
#         pass
