import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from apps.qna.models.answer.answers import Answer
from apps.qna.models.answer.comments import AnswerComment
from apps.qna.models.answer.images import AnswerImage
from apps.qna.models.question import Question, QuestionCategory
from apps.qna.serializers.answer.answers import (
    AdminAnswerDeleteResponseSerializer,
    AnswerAdoptRequestSerializer,
    AnswerAdoptResponseSerializer,
    AnswerCreateResponseSerializer,
    AnswerInputSerializer,
    AnswerSerializer,
)
from apps.qna.serializers.answer.author import AnswerAuthorSerializer
from apps.qna.serializers.answer.comments import (
    AnswerCommentSerializer,
    CommentCreateResponseSerializer,
)
from apps.qna.serializers.answer.images import (
    AnswerImagePresignedURLSerializer,
    AnswerImageSerializer,
)
from apps.user.models.user import RoleChoices, User

"""
Answer Serializer 테스트
- AnswerSerializer
- AnswerInputSerializer
- AnswerAuthorSerializer
- AnswerCommentSerializer
- AnswerImageSerializer
- AnswerImagePresignedURLSerializer
- Response Serializers
"""


class _QnADBBase(TestCase):
    """DB를 사용하는 테스트에서 공통으로 쓰는 최소 데이터"""

    user: User
    other_user: User
    password: str
    question_category: QuestionCategory
    question: Question
    answer: Answer

    @classmethod
    def setUpTestData(cls) -> None:
        from apps.qna.models.question import Question

        cls.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="testuser",
            nickname="테스터",
            role=RoleChoices.ST,
            birthday=datetime.date(2000, 1, 1),
        )

        cls.question_category = QuestionCategory.objects.create(
            name="test_category",
        )

        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.question_category,
            title="테스트 질문",
            content="질문 내용입니다.",
        )

        # ⚠️ 댓글/이미지는 공용으로 만들지 않음(각 테스트에서 생성)
        cls.answer = Answer.objects.create(
            author=cls.user,
            question=cls.question,
            content="답변 내용입니다.",
        )


"""
AnswerAuthorSerializer Tests
test_serializer_contains_expected_fields
    필요한 필드가 포함되어 있는지 확인
test_all_fields_are_read_only
    모든 필드가 read_only인지 확인
"""


class TestAnswerAuthorSerializer(_QnADBBase):

    def test_serializer_contains_expected_fields(self) -> None:
        serializer = AnswerAuthorSerializer(self.user)

        self.assertIn("id", serializer.data)
        self.assertIn("nickname", serializer.data)
        self.assertIn("profile_image_url", serializer.data)
        self.assertIn("role", serializer.data)

    def test_all_fields_are_read_only(self) -> None:
        serializer = AnswerAuthorSerializer()

        for field_name in ["id", "nickname", "profile_image_url", "role"]:
            self.assertTrue(serializer.fields[field_name].read_only)


"""
AnswerImageSerializer Tests
test_image_url_uses_s3_client
    image_url이 S3Client.build_url()을 사용하는지 확인
"""


class TestAnswerImageSerializer(_QnADBBase):

    @patch("apps.qna.serializers.answer.images.S3Client")
    def test_image_url_uses_s3_client(self, mock_s3_client: MagicMock) -> None:
        test_image = AnswerImage.objects.create(
            answer=self.answer,
            image_url="answer_images/test-uuid.jpg",
        )

        mock_instance = mock_s3_client.return_value
        mock_instance.build_url.return_value = "https://s3.example.com/answer_images/test-uuid.jpg"

        serializer = AnswerImageSerializer(test_image)

        self.assertEqual(serializer.data["id"], test_image.id)
        self.assertIn("https://s3.example.com", serializer.data["image_url"])
        mock_instance.build_url.assert_called_once_with(test_image.image_url)


"""
AnswerImagePresignedURLSerializer 테스트
test_valid_image_extensions
    유효한 이미지 확장자 허용
test_invalid_extensions_rejected
    유효하지 않은 확장자 거부
test_file_without_extension_rejected
    확장자 없는 파일명 거부
test_empty_file_name_rejected
    빈 파일명 거부
"""


class TestAnswerImagePresignedURLSerializer(SimpleTestCase):
    def test_valid_image_extensions(self) -> None:
        valid_names = [
            "image.png",
            "image.jpg",
            "image.jpeg",
            "image.gif",
            "image.webp",
            "IMAGE.PNG",  # 대문자도 허용
            "my-photo.JPEG",
        ]

        for file_name in valid_names:
            with self.subTest(file_name=file_name):
                serializer = AnswerImagePresignedURLSerializer(data={"file_name": file_name})
                self.assertTrue(serializer.is_valid())

    def test_invalid_extensions_rejected(self) -> None:
        invalid_names = [
            "document.pdf",
            "script.js",
            "style.css",
            "archive.zip",
            "video.mp4",
        ]

        for file_name in invalid_names:
            with self.subTest(file_name=file_name):
                serializer = AnswerImagePresignedURLSerializer(data={"file_name": file_name})
                self.assertFalse(serializer.is_valid())
                self.assertIn("file_name", serializer.errors)

    def test_file_without_extension_rejected(self) -> None:
        serializer = AnswerImagePresignedURLSerializer(data={"file_name": "noextension"})

        self.assertFalse(serializer.is_valid())
        self.assertIn("확장자가 포함된 파일명", str(serializer.errors["file_name"]))

    def test_empty_file_name_rejected(self) -> None:
        serializer = AnswerImagePresignedURLSerializer(data={"file_name": ""})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file_name", serializer.errors)


"""
AnswerCommentSerializer 테스트
test_serializer_contains_expected_fields
    필요한 필드가 포함되어 있는지 확인
test_author_is_nested_serializer
    author가 중첩 시리얼라이저인지 확인
test_content_validation
    content 필드 유효성 검사
"""


class TestAnswerCommentSerializer(_QnADBBase):
    def test_serializer_contains_expected_fields(self) -> None:
        test_comment = AnswerComment.objects.create(
            author=self.user,
            answer=self.answer,
            content="댓글 내용입니다.",
        )

        serializer = AnswerCommentSerializer(test_comment)

        self.assertIn("id", serializer.data)
        self.assertIn("author", serializer.data)
        self.assertIn("content", serializer.data)
        self.assertIn("created_at", serializer.data)

    def test_author_is_nested_serializer(self) -> None:
        test_comment = AnswerComment.objects.create(
            author=self.user,
            answer=self.answer,
            content="댓글 내용입니다.",
        )

        serializer = AnswerCommentSerializer(test_comment)

        self.assertIsInstance(serializer.data["author"], dict)
        self.assertIn("nickname", serializer.data["author"])

    def test_content_validation(self) -> None:
        serializer = AnswerCommentSerializer(data={"content": "테스트 댓글"})
        self.assertTrue(serializer.is_valid())


"""
CommentCreateResponseSerializer Tests
test_serializer_output_format
    응답 형식 확인
test_datetime_format
    datetime 포맷 확인 (YYYY-MM-DD HH:MM:SS)
"""


class TestCommentCreateResponseSerializer(_QnADBBase):
    def test_serializer_output_format(self) -> None:
        test_comment = AnswerComment.objects.create(
            author=self.user,
            answer=self.answer,
            content="댓글 내용입니다.",
        )

        serializer = CommentCreateResponseSerializer(test_comment)

        self.assertIn("comment_id", serializer.data)
        self.assertIn("answer_id", serializer.data)
        self.assertIn("author_id", serializer.data)
        self.assertIn("created_at", serializer.data)

    def test_datetime_format(self) -> None:
        test_comment = AnswerComment.objects.create(
            author=self.user,
            answer=self.answer,
            content="댓글 내용입니다.",
        )

        serializer = CommentCreateResponseSerializer(test_comment)

        created_at = serializer.data["created_at"]
        self.assertEqual(len(created_at), 19)
        self.assertIn("-", created_at)
        self.assertIn(":", created_at)


"""
AnswerInputSerializer Tests
test_valid_input
    유효한 입력 데이터
test_with_image_urls
    image_urls 포함된 입력
test_empty_content_rejected
    빈 content 거부
"""


class TestAnswerInputSerializer(SimpleTestCase):
    def test_valid_input(self) -> None:
        data = {"content": "답변 내용입니다."}
        serializer = AnswerInputSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["content"], "답변 내용입니다.")

    def test_with_image_urls(self) -> None:
        data = {
            "content": "답변 내용입니다.",
            "image_urls": ["image1.jpg", "image2.png"],
        }
        serializer = AnswerInputSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data["image_urls"]), 2)

    def test_empty_content_rejected(self) -> None:
        data = {"content": ""}
        serializer = AnswerInputSerializer(data=data)

        self.assertFalse(serializer.is_valid())


"""
AnswerSerializer 테스트
test_serializer_contains_expected_fields
     필요한 필드가 포함되어 있는지 확인
test_preview_comments_returns_max_3
     preview_comments는 최대 3개만 반환
test_total_comments_count
    total_comments_count가 정확한지 확인
test_is_adopted_read_only
    is_adopted 필드가 read_only인지 확인
"""


class TestAnswerSerializer(_QnADBBase):
    def test_serializer_contains_expected_fields(self) -> None:
        serializer = AnswerSerializer(self.answer)

        expected_fields = [
            "id",
            "author",
            "content",
            "images",
            "is_adopted",
            "created_at",
            "preview_comments",
            "total_comments_count",
        ]
        for field in expected_fields:
            self.assertIn(field, serializer.data)

    def test_preview_comments_returns_max_3(self) -> None:
        for i in range(5):
            AnswerComment.objects.create(
                author=self.user,
                answer=self.answer,
                content=f"댓글 {i + 1}",
            )

        serializer = AnswerSerializer(self.answer)

        self.assertEqual(len(serializer.data["preview_comments"]), 3)

    def test_total_comments_count(self) -> None:
        for i in range(5):
            AnswerComment.objects.create(
                author=self.user,
                answer=self.answer,
                content=f"댓글 {i + 1}",
            )

        self.answer.refresh_from_db()
        serializer = AnswerSerializer(self.answer)

        self.assertEqual(serializer.data["total_comments_count"], 5)

    def test_is_adopted_read_only(self) -> None:
        serializer = AnswerSerializer()
        self.assertIn("is_adopted", serializer.Meta.read_only_fields)


"""
AnswerAdoptRequestSerializer Tests
test_valid_input
    유효한 입력
test_missing_fields_rejected
    필수 필드 누락 시 거부
"""


class TestAnswerAdoptRequestSerializer(SimpleTestCase):
    def test_valid_input(self) -> None:
        data = {
            "question_id": 1,
            "answer_id": 1,
            "is_adopted": True,
        }
        serializer = AnswerAdoptRequestSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_missing_fields_rejected(self) -> None:
        data = {"question_id": 1}
        serializer = AnswerAdoptRequestSerializer(data=data)

        self.assertFalse(serializer.is_valid())


"""
Response Serializers 통합 테스트
AnswerUpdateResponseSerializer의 updated_at 항목을 어떻게 처리할 지 몰라서 스킵
updated_at = serializers.DateTimeField(
source="modified_at",
format="%Y-%m-%d %H:%M:%S",
)
이렇게 되어 있는데, modified_at을 어떻게 적용하죠?
"""


class TestResponseSerializers(_QnADBBase):
    def test_response_serializers_output_format(self) -> None:
        """✅ 각 Response Serializer의 필드 포함 여부 확인"""
        test_cases = [
            (
                AnswerCreateResponseSerializer,
                self.answer,
                ["answer_id", "question_id", "author_id", "created_at"],
            ),
            (
                AnswerAdoptResponseSerializer,
                self.answer,
                ["question_id", "answer_id", "is_adopted"],
            ),
            (
                AdminAnswerDeleteResponseSerializer,
                {"answer_id": 1, "deleted_comment_count": 5},
                ["answer_id", "deleted_comment_count"],
            ),
        ]

        for serializer_class, instance, expected_fields in test_cases:
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class(instance)
                for field in expected_fields:
                    self.assertIn(field, serializer.data)
