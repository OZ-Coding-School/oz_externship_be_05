from rest_framework import serializers
import json
from apps.exams.models import ExamQuestion

class ExamQuestionDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/v1/admin/exams/{exam_id} 요청 시 사용되는 목록 조회 시리얼라이저입니다.
    """
    question_id = serializers.IntegerField(source='id')     # question_id로 필드이름변경
    options = serializers.SerializerMethodField()           # json > list 변환을 위해 사용
    correct_answer = serializers.JSONField(source='answer')

    class Meta:
        model = ExamQuestion
        fields = [
            "question_id",
            "type",
            "question",
            "prompt",
            "point",
            "options",
            "correct_answer"
        ]

    def get_options(self, obj) -> list:
        """text 타입의 options_json을 파이썬 리스트로 변환"""
        if not obj.options_json:
            return []
        try:
            # DB의 text 데이터를 JSON 객체(리스트)로 파싱
            return json.loads(obj.options_json)
        except (ValueError, TypeError):
            return []