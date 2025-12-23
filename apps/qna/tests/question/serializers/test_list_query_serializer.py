from django.test import TestCase

from apps.qna.serializers.question.question_list_query import (
    QuestionListQuerySerializer,
)


class QuestionListQuerySerializerTests(TestCase):
    def test_valid_query(self) -> None:
        serializer = QuestionListQuerySerializer(
            data={
                "search_keyword": "django",
                "category_id": 1,
                "answer_status": "answered",
                "sort": "latest",
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_category_id_type(self) -> None:
        serializer = QuestionListQuerySerializer(
            data={
                "category_id": "invalid",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("category_id", serializer.errors)
