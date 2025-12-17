from django.test import TestCase

from apps.qna.serializers.question.question_list_query import (
    QuestionListQuerySerializer,
)


class QuestionListQuerySerializerTests(TestCase):
    def test_valid_query(self) -> None:
        serializer = QuestionListQuerySerializer(
            data={
                "answered": True,
                "page": 1,
                "page_size": 10,
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_page(self) -> None:
        serializer = QuestionListQuerySerializer(data={"page": 0})

        self.assertFalse(serializer.is_valid())
