from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from django.db import transaction

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import QuestionType
from apps.exams.models.exam_submission import ExamSubmission


def normalize_answers(
    deployment: ExamDeployment,
    raw_answers: Dict[str, Any],
) -> Dict[int, Any]:
    """
    - FE에서 온 answers를 question_id 기준 dict로 정규화하고
    - 응시 대상 deployment에 포함된 모든 문항에 대해 키를 채워준다.
    """
    answers_by_qid = {
        item["question_id"]: item.get("answer") for item in raw_answers.get("questions", []) if "question_id" in item
    }

    normalized: Dict[int, Any] = {}

    questions_qs = deployment.exam.questions.all()

    for question in questions_qs:
        normalized[question.id] = answers_by_qid.get(question.id)

    return normalized


def evaluate_submission(
    deployment: ExamDeployment,
    normalized_answers: Dict[int, Any],
) -> Tuple[int, int]:
    """
    자동 채점: 총점, 정답 개수 반환
    """
    total_score = 0
    correct_count = 0

    questions_qs = deployment.exam.questions.all()

    for question in questions_qs:
        user_answer = normalized_answers.get(question.id)
        correct_answer = question.answer
        question_type = question.type
        question_point = question.point

        is_correct = False

        # 단일 선택
        if question_type == QuestionType.SINGLE_CHOICE:
            is_correct = user_answer == correct_answer

        # 다중 선택
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            if isinstance(user_answer, list) and isinstance(correct_answer, list):
                is_correct = set(user_answer) == set(correct_answer)

        # OX
        elif question_type == QuestionType.OX:
            is_correct = user_answer == correct_answer

        # 단답형
        elif question_type == QuestionType.SHORT_ANSWER:
            if isinstance(user_answer, str) and isinstance(correct_answer, str):
                is_correct = user_answer.strip() == correct_answer.strip()

        # 순서 정렬
        elif question_type == QuestionType.ORDERING:
            is_correct = user_answer == correct_answer

        # 빈칸 채우기
        elif question_type == QuestionType.FILL_BLANK:
            # 예: correct_answer = ["A", "B"]
            # user_answer = ["A", "B"]
            if isinstance(user_answer, list) and isinstance(correct_answer, list):
                is_correct = user_answer == correct_answer

        # 정답인 경우 채점
        if is_correct:
            correct_count += 1
            total_score += question_point

    return total_score, correct_count


@transaction.atomic
def create_exam_submission(
    *,
    deployment: ExamDeployment,
    submitter: Any,
    started_at: datetime,
    cheating_count: int,
    raw_answers: Dict[str, Any],
) -> ExamSubmission:
    normalized_answers = normalize_answers(deployment, raw_answers)
    score, correct_answer_count = evaluate_submission(deployment, normalized_answers)

    submission = ExamSubmission.objects.create(
        submitter=submitter,
        deployment=deployment,
        started_at=started_at,
        cheating_count=cheating_count,
        answers={"questions": [{"question_id": qid, "answer": answer} for qid, answer in normalized_answers.items()]},
        score=score,
        correct_answer_count=correct_answer_count,
    )

    return submission
