import datetime
from unittest.mock import patch

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.test import APITestCase

from apps.qna.models.answer.answers import Answer
from apps.qna.models.answer.comments import AnswerComment
from apps.qna.models.answer.images import AnswerImage
from apps.qna.models.question import Question, QuestionCategory
from apps.qna.services.answer.service import AnswerService, CommentService
from apps.user.models.user import RoleChoices, User


class TestQnAServiceUltimateCoverage(APITestCase):
    user: User
    other_user: User
    cat: QuestionCategory
    q: Question
    ans: Answer

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            name="테스터",
            nickname="테스터닉",
            role=RoleChoices.ST,
            birthday=datetime.date(2000, 1, 1),
        )
        cls.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            name="다른유저",
            nickname="다른닉",
            role=RoleChoices.ST,
            birthday=datetime.date(2000, 1, 1),
        )
        cls.cat = QuestionCategory.objects.create(name="cat")
        cls.q = Question.objects.create(author=cls.user, category=cls.cat, title="Q", content="C")
        cls.ans = Answer.objects.create(author=cls.user, question=cls.q, content="Ans")

    def setUp(self) -> None:
        self.patcher = patch("apps.core.utils.s3_client.S3Client.upload", return_value="fake_key")
        self.patcher_url = patch(
            "apps.core.utils.s3_client.S3Client.generate_presigned_url", return_value="http://fake.url"
        )
        self.patcher.start()
        self.patcher_url.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.patcher_url.stop()

    def test_complete_logic_paths(self) -> None:
        with self.assertRaises(NotFound):
            AnswerService.create_answer(self.user, 99999, "X")

        ans = AnswerService.create_answer(self.user, self.q.id, "img answer_images/1.jpg")
        self.assertEqual(ans.images.count(), 1)

        with self.assertRaises(ValidationError):
            AnswerService.update_answer(self.other_user, ans, "U")

        AnswerImage.objects.create(answer=ans, image_url="answer_images/stay.jpg")
        AnswerService.update_answer(self.user, ans, "answer_images/stay.jpg answer_images/new.png")
        ans.refresh_from_db()
        self.assertEqual(ans.images.count(), 2)

        ans2 = Answer.objects.create(author=self.other_user, question=self.q, content="A")
        AnswerService.toggle_adoption(self.user, self.q.id, ans2.id)
        ans2.refresh_from_db()
        self.assertTrue(ans2.is_adopted)

        cmt = CommentService.create_comment(self.user, self.q.id, ans2.id, "C")
        CommentService.update_comment(self.user, cmt, "U")
        CommentService.delete_comment(self.user, cmt)

        self.assertEqual(AnswerService._extract_image_keys(None), set())
