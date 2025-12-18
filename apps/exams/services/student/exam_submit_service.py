from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from django.db import transaction
from rest_framework import serializers

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import QuestionType
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models import User


# 시험 제출 2회 제한
def validate_exam_submission_limit(
    *,
    deployment: ExamDeployment,
    submitter: User,
) -> None:
    # 시험은 최대 2회까지 제출 가능
    existing_count = ExamSubmission.objects.filter(
        deployment=deployment,
        submitter=submitter,
    ).count()

    if existing_count >= 2:
        raise serializers.ValidationError({"error_detail": "이미 제출된 시험입니다."})


def _snapshot_questions(deployment: ExamDeployment) -> List[Dict[str, Any]]:
    # 배포 스냅샷에서 문항 가져오기
    snapshot_json = deployment.questions_snapshot or {}
    # snapshot = json.loads(cast(str, snapshot_json))

    questions = snapshot_json.get("questions", [])
    if not isinstance(questions, list):
        return []
    return questions


def normalize_answers(
    deployment: ExamDeployment,
    raw_answers: Dict[str, Any],
) -> Dict[int, Any]:
    # FE answers -> qid 기준 dict
    answers_by_qid: Dict[int, Any] = {}
    for item in raw_answers.get("questions", []):
        if "question_id" in item:
            answers_by_qid[int(item["question_id"])] = item.get("answer")

    # deployment에 포함된 모든 문항 qid를 채워넣기 (없는 건 None)
    normalized: Dict[int, Any] = {}
    for q in _snapshot_questions(deployment):
        qid = int(q["question_id"])
        normalized[qid] = answers_by_qid.get(qid)

    return normalized


def evaluate_submission(
    deployment: ExamDeployment,
    normalized_answers: Dict[int, Any],
) -> Tuple[int, int]:
    total_score = 0
    correct_count = 0

    for q in _snapshot_questions(deployment):
        qid = int(q["question_id"])
        user_answer = normalized_answers.get(qid)
        correct_answer = q.get("answer")
        question_type = q.get("type")
        question_point = int(q.get("point", 0))

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
            if isinstance(user_answer, list) and isinstance(correct_answer, list):
                is_correct = user_answer == correct_answer

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
    validate_exam_submission_limit(deployment=deployment, submitter=submitter)

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
