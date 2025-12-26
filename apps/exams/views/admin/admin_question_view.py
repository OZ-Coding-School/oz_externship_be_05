from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions.exception_messages import EMS
from apps.exams.permissions.admin_permission import AdminUserPermissionView
from apps.exams.serializers.admin.admin_question_serializer import (
    AdminExamQuestionSerializer,
)
from apps.exams.services.admin.admin_question_service import AdminQuestionService

# 공통으로 사용할 예시 데이터 정의
QUESTION_EXAMPLES = [
    OpenApiExample(
        "단일 선택형 예시",
        summary="단일 선택 (single_choice)",
        value={
            "type": "single_choice",
            "question": "파이썬의 창시자는 누구인가요?",
            "prompt": "",
            "options": ["귀도 반 로섬", "제임스 고슬링", "데니스 리치", "브렌던 아이크"],
            "blank_count": 0,
            "correct_answer": ["귀도 반 로섬"],
            "point": 5,
            "explanation": "파이썬은 1991년 귀도 반 로섬에 의해 발표되었습니다.",
        },
    ),
    OpenApiExample(
        "다중 선택형 예시",
        summary="다중 선택 (multiple_choice)",
        value={
            "type": "multiple_choice",
            "question": "다음 중 TypeScript의 특징으로 올바른 것을 모두 고르시오.",
            "prompt": "",
            "options": [
                "정적 타입 검사 지원",
                "런타임 시에만 타입 검사",
                "자바스크립트와 호환됨",
                "브라우저가 직접 실행함",
            ],
            "blank_count": 0,
            "correct_answer": ["정적 타입 검사 지원", "자바스크립트와 호환됨"],
            "point": 10,
            "explanation": "TypeScript는 정적 타입 검사 및 JS 상위 호환 언어입니다.",
        },
    ),
    OpenApiExample(
        "O/X 퀴즈 예시",
        summary="O/X 퀴즈 (ox)",
        value={
            "type": "ox",
            "question": "파이썬은 컴파일 언어이다.",
            "prompt": "",
            "options": ["O", "X"],
            "blank_count": 0,
            "correct_answer": ["X"],  # 통일성을 위해 리스트로 유지하거나 모델 필드에 맞춤
            "point": 5,
            "explanation": "파이썬은 대표적인 인터프리터 언어입니다.",
        },
    ),
    OpenApiExample(
        "단답형 예시",
        summary="단답형 (short_answer)",
        value={
            "type": "short_answer",
            "question": "Django에서 데이터베이스 구조를 관리하기 위해 사용하는 명령어로, 모델의 변경사항을 파일로 생성하는 명령어는 무엇인가요?",
            "prompt": "",
            "options": None,
            "blank_count": 0,
            "correct_answer": ["makemigrations"],
            "point": 10,
            "explanation": "변경사항 생성은 makemigrations, 반영은 migrate입니다.",
        },
    ),
    OpenApiExample(
        "순서 정렬형 예시",
        summary="순서 정렬형 (ordering)",
        value={
            "type": "ordering",
            "question": "Dockerfile 빌드 순서를 정렬하세요.",
            "prompt": "",
            "options": ["Dockerfile 작성", "이미지 빌드", "컨테이너 실행"],
            "blank_count": 0,
            "correct_answer": ["Dockerfile 작성", "이미지 빌드", "컨테이너 실행"],
            "point": 10,
            "explanation": "표준적인 컨테이너 배포 순서입니다.",
        },
    ),
    OpenApiExample(
        "빈칸 채우기 예시",
        summary="빈칸 채우기 (fill_blank)",
        value={
            "type": "fill_blank",
            "question": "다음 문장의 빈칸을 채우세요.",
            "prompt": "Django는 파이썬 기반의 ( ) 웹 프레임워크이다.",
            "options": None,
            "blank_count": 1,
            "correct_answer": ["풀스택"],
            "point": 5,
            "explanation": "Django는 다양한 기능을 제공하는 풀스택 프레임워크입니다.",
        },
    ),
]


class ExamAdminQuestionCreateAPIView(AdminUserPermissionView):
    """쪽지시험 문제 등록 API"""

    service = AdminQuestionService()

    @extend_schema(
        tags="쪽지시험 관리",
        summary="쪽지시험 문제 등록",
        description="특정 쪽지시험에 새로운 문제를 추가합니다. 한 시험당 최대 20개, 총 배점 100점 제한이 있습니다.",
        request=AdminExamQuestionSerializer,
        examples=QUESTION_EXAMPLES,
        responses={
            201: AdminExamQuestionSerializer,
            400: OpenApiResponse(description="유효하지 않은 문제 등록 데이터입니다."),
            404: OpenApiResponse(description="해당 쪽지시험 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="문제 수 또는 총 배점 초과"),
        },
    )
    def post(self, request: Request, exam_id: int) -> Response:
        serializer = AdminExamQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # 서비스 레이어에서 비즈니스 로직(제한 사항 체크) 수행
            question = self.service.create_question(exam_id, serializer.validated_data)
            # 반환 시에는 최신 데이터가 반영된 시리얼라이저 사용
            return Response(AdminExamQuestionSerializer(question).data, status=status.HTTP_201_CREATED)
        except NotFound:
            return Response(EMS.E404_NOT_FOUND("해당 쪽지시험 정보"), status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response(EMS.E409_QUIZ_LIMIT_EXCEEDED_REG, status=status.HTTP_409_CONFLICT)


class ExamAdminQuestionUpdateDestroyAPIView(AdminUserPermissionView):
    """쪽지시험 문제 수정 및 삭제 API"""

    service = AdminQuestionService()

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 문제 수정",
        description="기존 문제를 수정합니다. 문제 유형 변경 및 배점 수정 시 상한선 검증이 다시 수행됩니다.",
        request=AdminExamQuestionSerializer,
        examples=QUESTION_EXAMPLES,
        responses={
            200: AdminExamQuestionSerializer,
            400: OpenApiResponse(description="유효하지 않은 문제 수정 데이터입니다."),
            404: OpenApiResponse(description="수정하려는 문제 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="문제 수 또는 총 배점 초과"),
        },
    )
    def patch(self, request: Request, question_id: int) -> Response:
        # partial=True를 통해 일부 필드만 수정하는 것 허용
        serializer = AdminExamQuestionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            question = self.service.update_question(question_id, serializer.validated_data)
            return Response(AdminExamQuestionSerializer(question).data, status=status.HTTP_200_OK)
        except NotFound:
            return Response(EMS.E404_NOT_FOUND("수정하려는 문제 정보"), status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response(EMS.E409_QUIZ_LIMIT_EXCEEDED_EDIT, status=status.HTTP_409_CONFLICT)

    @extend_schema(
        tags=["쪽지시험 관리"],
        summary="쪽지시험 문제 삭제",
        responses={
            204: OpenApiResponse(description="삭제 성공"),
            404: OpenApiResponse(description="삭제할 문제 정보를 찾을 수 없습니다."),
        },
    )
    def delete(self, request: Request, question_id: int) -> Response:
        try:
            self.service.delete_question(question_id)
            # 삭제 성공 시 204 No Content 반환 (명세서에 따라 200 OK로 변경 가능)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            return Response(EMS.E404_NOT_FOUND("삭제할 문제 정보"), status=status.HTTP_404_NOT_FOUND)
