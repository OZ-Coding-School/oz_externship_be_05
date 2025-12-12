from typing import Any

from django.test import TestCase

from apps.exams.serializers.student.exam_question_serializer import (
    ExamQuestionSerializer,
)


class ExamQuestionSerializerTest(TestCase):

    def setUp(self) -> None:
        """테스트에 사용될 더미 데이터를 준비합니다."""
        self.question_data = {
            "question_id": 42,
            "question_type": "multiple_choice",
            "content": "다음 중 파이썬의 자료형이 아닌 것은?",
            "options": ["int", "str", "list", "array"],
        }

    def test_valid_data_output(self) -> None:
        """유효한 데이터가 시리얼라이저를 통해 올바르게 출력되는지 확인합니다."""
        serializer = ExamQuestionSerializer(data=self.question_data)

        self.assertTrue(serializer.is_valid())
        data: Any = serializer.data

        self.assertEqual(data["question_id"], 42)

    def test_options_optional(self) -> None:
        """options 필드가 없어도 유효한지 확인합니다 (단답형 등을 가정)."""
        data_no_options = {
            "question_id": 100,
            "question_type": "short_answer",
            "content": "대한민국의 수도는?",
        }
        serializer = ExamQuestionSerializer(data=data_no_options)

        self.assertTrue(serializer.is_valid())
