from django.test import TestCase

from apps.qna.models import Question, QuestionCategory
from apps.qna.serializers.question.question_update import QuestionUpdateSerializer


class QuestionUpdateSerializerTest(TestCase):
    def setUp(self) -> None:
        self.category = QuestionCategory.objects.create(name="백엔드")

    # 부분 수정 검증 (성공)
    def test_partial_update_valid(self) -> None:
        serializer = QuestionUpdateSerializer(data={"title": "변경"}, partial=True)
        self.assertTrue(serializer.is_valid())

    # 이미지 태그가 포함된 content가 잘 들어가는지 확인
    def test_content_update_with_image_tag(self) -> None:
        html_content = '이미지 <img src="https://test.com/a.png">'

        serializer = QuestionUpdateSerializer(data={"content": html_content}, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["content"], html_content)
