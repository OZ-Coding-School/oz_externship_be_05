import re
from typing import TYPE_CHECKING, Any, Dict, List, Set, cast

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.core.exceptions.exception_messages import EMS
from apps.qna.models.answer.answers import Answer
from apps.qna.models.answer.comments import AnswerComment
from apps.qna.models.answer.images import AnswerImage
from apps.qna.models.question import Question

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

    UserType = AbstractBaseUser | AnonymousUser
    RealUser = Any
else:
    UserType = Any
    RealUser = Any


class AnswerService:
    """
    Answer 도메인의 비즈니스 로직 담당
    """

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    @staticmethod
    def create_answer(user: UserType, question_id: int, content: str) -> Answer:
        question = get_object_or_404(Question, pk=question_id)
        real_user = cast(RealUser, user)

        with transaction.atomic():
            answer: Answer = Answer.objects.create(
                author=real_user,
                question=question,
                content=content,
            )
            AnswerService._process_images_for_create(answer, content)
            return answer

    @staticmethod
    def update_answer(user: UserType, answer: Answer, content: str) -> Answer:
        if answer.author != user:
            raise ValidationError(EMS.E403_OWNER_ONLY_EDIT("답변"))

        with transaction.atomic():
            answer.content = content
            answer.save()
            AnswerService._sync_images_for_update(answer, content)
            return answer

    @staticmethod
    def delete_answer(user: UserType, answer: Answer) -> None:
        if answer.author != user:
            raise ValidationError(EMS.E403_PERMISSION_DENIED("삭제"))
        answer.delete()

    @staticmethod
    def delete_answer_by_admin(user: UserType, answer_id: int) -> Dict[str, int]:
        answer = get_object_or_404(Answer, pk=answer_id)
        comment_count: int = answer.comments.count()
        deleted_id: int = answer.id

        answer.delete()

        return {
            "answer_id": deleted_id,
            "deleted_comment_count": comment_count,
        }

    @staticmethod
    def toggle_adoption(user: UserType, answer_id: int) -> Answer:
        answer = get_object_or_404(Answer, pk=answer_id)
        question: Question = answer.question

        if question.author != user:
            raise ValidationError(EMS.E403_QNA_PERMISSION_DENIED("답변 채택"))

        if answer.author == user:
            raise ValidationError(EMS.E403_ADOPT_OWNER_ONLY)

        with transaction.atomic():
            if answer.is_adopted:
                answer.is_adopted = False
            else:
                if question.answers.filter(is_adopted=True).exists():
                    raise ValidationError(EMS.E409_ALREADY_ADOPTED)
                answer.is_adopted = True

            answer.save()
            return answer

    @staticmethod
    def _extract_image_keys(content: str) -> Set[str]:
        if not content:
            return set()

        raw_keys: List[str] = re.findall(
            r'answer_images/[^\s"\')>]+',
            content,
        )
        clean_keys: Set[str] = set()

        for key in raw_keys:
            key = key.split("?", 1)[0]

            if "." in key:
                ext = key.rsplit(".", 1)[-1].lower()
                if ext in AnswerService.ALLOWED_IMAGE_EXTENSIONS:
                    clean_keys.add(key)

        return clean_keys

    @staticmethod
    def _process_images_for_create(answer: Answer, content: str) -> None:
        current_keys = AnswerService._extract_image_keys(content)

        if current_keys:
            images = [AnswerImage(answer=answer, image_url=key) for key in current_keys]
            AnswerImage.objects.bulk_create(images)

    @staticmethod
    def _sync_images_for_update(answer: Answer, content: str) -> None:
        current_keys = AnswerService._extract_image_keys(content)

        db_keys_qs = AnswerImage.objects.filter(
            answer=answer,
        ).values_list("image_url", flat=True)
        db_keys: Set[str] = set(db_keys_qs)

        keys_to_delete = db_keys - current_keys
        keys_to_create = current_keys - db_keys

        if keys_to_delete:
            AnswerImage.objects.filter(
                answer=answer,
                image_url__in=keys_to_delete,
            ).delete()

        if keys_to_create:
            images = [AnswerImage(answer=answer, image_url=key) for key in keys_to_create]
            AnswerImage.objects.bulk_create(images)


class CommentService:
    @staticmethod
    def create_comment(
        user: UserType,
        answer_id: int,
        content: str,
    ) -> AnswerComment:
        answer = get_object_or_404(Answer, pk=answer_id)
        real_user = cast(RealUser, user)

        return AnswerComment.objects.create(
            author=real_user,
            answer=answer,
            content=content,
        )

    @staticmethod
    def update_comment(
        user: UserType,
        comment: AnswerComment,
        content: str,
    ) -> AnswerComment:
        if comment.author != user:
            raise ValidationError(EMS.E403_OWNER_ONLY_EDIT("댓글"))

        comment.content = content
        comment.save()
        return comment

    @staticmethod
    def delete_comment(
        user: UserType,
        comment: AnswerComment,
    ) -> None:
        if comment.author != user:
            raise ValidationError(EMS.E403_PERMISSION_DENIED("삭제"))
        comment.delete()
