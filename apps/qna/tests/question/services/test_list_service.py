from datetime import timedelta
from typing import cast

from django.test import TestCase
from django.utils import timezone

from apps.qna.exceptions.question_exceptions import QuestionListEmptyError
from apps.qna.models import Question, QuestionCategory, QuestionImage
from apps.qna.models.question.question_base import QuestionAnnotated
from apps.qna.services.question.question_list.service import get_question_list
from apps.user.models.user import RoleChoices, User


class QuestionListServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="servicetest@test.com",
            password="test1234",
            name="유저",
            role=RoleChoices.ST,
            phone_number="010-0000-0000",
            gender="M",
            birthday="2000-01-01",
        )

        self.root_category = QuestionCategory.objects.create(name="백엔드")
        self.child_category = QuestionCategory.objects.create(
            name="Django",
            parent=self.root_category,
        )

    def create_question(
        self,
        *,
        title: str,
        category: QuestionCategory,
        content: str = "내용입니다",
    ) -> Question:
        return Question.objects.create(
            author=self.user,
            title=title,
            content=content,
            category=category,
            created_at=timezone.now(),
        )

    # 질문이 없으면 예외 발생
    def test_no_questions(self) -> None:
        with self.assertRaises(QuestionListEmptyError):
            get_question_list(
                page=1,
                size=10,
            )

    # 기본 목록 조회 성공
    def test_get_question_list_success(self) -> None:
        self.create_question(
            title="질문1",
            category=self.child_category,
        )

        questions, page_info = get_question_list(
            page=1,
            size=10,
        )

        self.assertEqual(len(questions), 1)
        self.assertEqual(page_info["total_count"], 1)

    # answered 필터(True/False)
    def test_filter_by_answered_true(self) -> None:
        question = self.create_question(
            title="답변 질문",
            category=self.child_category,
        )

        question.answers.create(
            author=self.user,
            content="답변",
        )

        questions, _ = get_question_list(
            answer_status="answered",
            page=1,
            size=10,
        )

        self.assertEqual(len(questions), 1)

    # category 필터 (부모 선택 시 자식 포함)
    def test_filter_by_category_include_children(self) -> None:
        self.create_question(
            title="Django 질문",
            category=self.child_category,
        )

        # "_" = get_question_list의 반환값을 받긴하지만 사용X
        questions, _ = get_question_list(
            category_id=self.root_category.id,
            page=1,
            size=10,
        )

        self.assertEqual(len(questions), 1)

    # 검색 필터
    def test_filter_by_search(self) -> None:
        self.create_question(
            title="Django 질문",
            category=self.child_category,
        )
        self.create_question(
            title="FastAPI 질문",
            category=self.child_category,
        )

        questions, _ = get_question_list(
            search_keyword="Django",
            page=1,
            size=10,
        )

        self.assertEqual(len(questions), 1)
        self.assertIn("Django", questions[0].title)

    # 정렬 필터 - latest
    def test_sort_latest(self) -> None:
        q1 = self.create_question(
            title="오래된 질문",
            category=self.child_category,
        )
        q1.created_at = timezone.now() - timedelta(days=1)
        q1.save(update_fields=["created_at"])

        q2 = self.create_question(
            title="최신 질문",
            category=self.child_category,
        )

        questions, _ = get_question_list(
            sort="latest",
            page=1,
            size=10,
        )

        self.assertEqual(questions[0].id, q2.id)

    # 정렬 필터 - oldest
    def test_sort_oldest(self) -> None:
        q1 = self.create_question(
            title="오래된 질문",
            category=self.child_category,
        )
        q1.created_at = timezone.now() - timedelta(days=1)
        q1.save(update_fields=["created_at"])

        q2 = self.create_question(
            title="최신 질문",
            category=self.child_category,
        )

        questions, _ = get_question_list(
            sort="oldest",
            page=1,
            size=10,
        )

        self.assertEqual(questions[0].id, q1.id)

    # 정렬 필터 - views
    def test_sort_views(self) -> None:
        q1 = self.create_question(
            title="조회수 적음",
            category=self.child_category,
        )
        q1.view_count = 10
        q1.save(update_fields=["view_count"])

        q2 = self.create_question(
            title="조회수 많음",
            category=self.child_category,
        )
        q2.view_count = 50
        q2.save(update_fields=["view_count"])

        questions, _ = get_question_list(
            sort="views",
            page=1,
            size=10,
        )

        self.assertEqual(questions[0].id, q2.id)

    # thumbnail_image_url 서브쿼리
    def test_thumbnail_image_annotation(self) -> None:
        question = self.create_question(
            title="이미지 질문",
            category=self.child_category,
        )

        QuestionImage.objects.create(
            question=question,
            img_url="https://example.com/image1.png",
        )

        questions, _ = get_question_list(
            page=1,
            size=10,
        )

        # mypy만족을 위해 추가
        annotated_question = cast(QuestionAnnotated, questions[0])

        self.assertEqual(
            annotated_question.thumbnail_image_url,
            "https://example.com/image1.png",
        )
