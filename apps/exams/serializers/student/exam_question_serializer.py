from typing import Any, Optional

from rest_framework import serializers


class ExamQuestionSerializer(serializers.Serializer[Any]):
    """
    쪽지시험 문제 조회 응답 시리얼라이저
    """

    question_id = serializers.IntegerField(source="id")
    number = serializers.SerializerMethodField()  # 번호 계산
    type = serializers.CharField()
    question = serializers.CharField()
    point = serializers.IntegerField()
    prompt = serializers.CharField(allow_null=True, required=False)
    blank_count = serializers.IntegerField(allow_null=True, required=False)
    options = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    answer_input = serializers.SerializerMethodField()

    def get_number(self, obj: Any) -> int:
        # context에서 문제 리스트 가져와 순번 계산
        questions_list = self.context.get("questions_list", [])
        for idx, q in enumerate(questions_list, start=1):
            if q.id == obj.id:
                return idx
        return 0

    def get_answer_input(self, obj: Any) -> Optional[Any]:
        # FILL_BLANK는 개수만큼 빈 문자열 배열 반환
        if obj.type == "fill_blank" and getattr(obj, "blank_count", None):
            return [""] * obj.blank_count
        if obj.type in ["multiple_choice", "ordering"]:
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

    def to_representation(self, instance: dict[str, Any]) -> dict[str, Any]:

        return {
            "exam_id": instance["exam_id"],
            "exam_name": instance["exam_name"],
            "duration_time": instance["duration_time"],
            "elapsed_time": instance["elapsed_time"],
            "cheating_count": instance["cheating_count"],
            "questions": ExamQuestionSerializer(
                instance["questions"], many=True, context={"questions_list": instance["questions"]}
            ).data,
        }
