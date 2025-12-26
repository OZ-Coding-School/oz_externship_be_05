from typing import Any, Optional

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import NotFound, ValidationError

from apps.exams.models import Exam, ExamQuestion


class AdminQuestionService:

    @transaction.atomic
    def delete_question(self, question_id: int) -> None:
        question_exists = ExamQuestion.objects.filter(id=question_id).exists()
        if not question_exists:
            raise NotFound()

        ExamQuestion.objects.filter(id=question_id).delete()
