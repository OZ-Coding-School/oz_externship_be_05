from typing import Any

from rest_framework import serializers

from apps.core.exceptions.exception_messages import EMS
from apps.exams.models import ExamQuestion, QuestionType


class ExamQuestionDetailSerializer(serializers.ModelSerializer[ExamQuestion]):
    """
    GET /api/v1/admin/exams/{exam_id} 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    """

    options = serializers.JSONField()  # JSONField(options)는 이미 파이썬 리스트
    correct_answer = serializers.JSONField(source="answer")

    class Meta:
        model = ExamQuestion
        fields = ["id", "type", "question", "prompt", "point", "options", "correct_answer", "explanation"]


class AdminExamQuestionSerializer(serializers.ModelSerializer[ExamQuestion]):
    """
    /api/v1/admin/exams/{exam_id}/questions
    /api/v1/admin/exams/questions/{question_id}
    관리자용 쪽지시험 문제 CUD 시리얼라이저
    """

    options = serializers.JSONField(required=False, allow_null=True)
    correct_answer = serializers.JSONField(source="answer")  #  요구사항 필드명
    explanation = serializers.CharField(required=False, allow_blank=True)

    exam_id = serializers.IntegerField(source="exam.id", read_only=True)

    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam_id",
            "type",
            "question",
            "prompt",
            "options",
            "blank_count",
            "correct_answer",
            "point",
            "explanation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "exam_id", "created_at", "updated_at"]

    def validate_point(self, value: int) -> int:
        if not (1 <= value <= 10):
            raise serializers.ValidationError(EMS.E400_LENGTH_LIMIT("배점", 1, 10))
        return value

    def _to_list(self, value: Any) -> list[Any]:
        """
        데이터를 일관되게 리스트로 변환하는 헬퍼 메서드
        리스트([])로 일관되게 처리
        1. {"A", "B"} (Set) -> ["A", "B"] (JSON 저장 가능 형태)
        2. "A" (단일값) -> ["A"]
        3. ["A", "B"] (리스트) -> ["A", "B"]
        4. True (Boolean) -> [True]
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (set, tuple)):
            return list(value)
        return [value] if value else []

    def validate_options(self, value: Any) -> list[Any]:
        """options를 무조건 리스트로 반환"""
        return self._to_list(value)

    def validate_correct_answer(self, value: Any) -> list[Any]:
        """correct_answer를 무조건 리스트로 반환"""
        return self._to_list(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
        문제 유형(type)별 필수 필드 유효성 검사
        """

        question_type = attrs.get("type")
        options = attrs.get("options")  # source="options_json"이므로 attrs에는 options_json으로 들어옴
        blank_count = attrs.get("blank_count")

        if question_type in [QuestionType.MULTIPLE_CHOICE, QuestionType.ORDERING]:  # 다지선다형, 순서정렬형
            if not options or not isinstance(options, list) or len(options) < 2:
                raise serializers.ValidationError({"options": "보기를 2개 이상 입력해야 합니다."})

        elif question_type == QuestionType.FILL_BLANK:  # 빈칸 채우기
            if blank_count is None or blank_count < 1 or blank_count > 5:
                raise serializers.ValidationError(
                    {"blank_count": "빈칸 개수는 최소 1개 이상, 최대 5개 이하여야 합니다."}
                )

        return attrs
