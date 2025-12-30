from typing import Any, Optional

from rest_framework import serializers


class ExamQuestionSerializer(serializers.Serializer[Any]):
    """
    쪽지시험 문제 조회 응답 시리얼라이저
    """

    question_id = serializers.IntegerField()  # 스냅샷에 저장된 question_id
    number = serializers.IntegerField()  # 뷰에서 미리 계산된 번호 사용
    type = serializers.CharField()
    question = serializers.CharField()
    point = serializers.IntegerField()
    prompt = serializers.CharField(allow_null=True, required=False)
    blank_count = serializers.IntegerField(allow_null=True, required=False)
    options = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    answer_input = serializers.SerializerMethodField()

    def get_answer_input(self, obj: dict[str, Any]) -> Optional[Any]:
        # FILL_BLANK는 개수만큼 빈 문자열 배열 반환
        if obj.get("type") == "fill_blank" and obj.get("blank_count"):
            return [""] * obj["blank_count"]
        if obj.get("type") in ["multiple_choice", "ordering"]:
            # MULTIPLE_CHOICE는 빈 배열, ORDERING은 빈 배열 (후에 순서 채우기)
            return []
        return None


class ExamQuestionResponseSerializer(serializers.Serializer[Any]):
    """
    쪽지시험 응시 문제풀이 전체 응답 시리얼라이저
    """

    exam_id = serializers.IntegerField()
    exam_name = serializers.CharField()
    duration_time = serializers.IntegerField()
    elapsed_time = serializers.IntegerField()
    cheating_count = serializers.IntegerField()
    questions = ExamQuestionSerializer(many=True)
