from django.test import TestCase

from apps.qna.serializers.question.question_update import QuestionUpdateSerializer


class QuestionUpdateSerializerTest(TestCase):

    # 부분 수정 검증
    def test_partial_update_valid(self) -> None:
        serializer = QuestionUpdateSerializer(data={"title": "변경"})
        self.assertTrue(serializer.is_valid())

    # 이미지 수정 검증
    def test_image_patch_valid(self) -> None:
        serializer = QuestionUpdateSerializer(
            data={
                "images": {
                    "delete_ids": [1, 2],
                    "add_urls": ["https://img.com/1.png"],
                }
            }
        )
        self.assertTrue(serializer.is_valid())
