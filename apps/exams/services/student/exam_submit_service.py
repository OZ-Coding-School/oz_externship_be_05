from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models import User


def validate_submission_time_limit(deployment: ExamDeployment) -> None:
    now = timezone.now()
    if not deployment.open_at < now < deployment.close_at:
        raise ValidationError("시험 문제풀이 결과를 제출가능한 시간이 아닙니다.")


def validate_exam_total_seconds(deployment: ExamDeployment, started_at: datetime) -> None:
    # 시간 제한 검증
    now = timezone.now()
    elapsed_seconds = int((now - started_at).total_seconds())

    if elapsed_seconds > deployment.duration_time:
        raise ValidationError("시험 제한 시간이 초과되어 제출할 수 없습니다")


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
        raise ValidationError("시험은 2회까지 제출 가능합니다.")


def _snapshot_questions(deployment: ExamDeployment) -> list[dict[str, Any]]:
    # 배포 스냅샷에서 문항 가져오기
    snapshot_json = deployment.questions_snapshot or {}
    questions = snapshot_json.get("questions", [])
    if not isinstance(questions, list):
        return []
    return questions


def grade_answers(
    deployment: ExamDeployment,
    submitted_answers: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int]:
    simplified_question_snapshot = _simplify_question_snapshot(deployment)
    total_score = 0
    correct_count = 0
    graded_answers = []
    for a in submitted_answers:
        question = simplified_question_snapshot[a["question_id"]]
        is_correct = set(a["submitted_answer"]) == set(question["answer"])
        if is_correct:
            total_score += question["point"]
            correct_count += 1
        a.update({"is_correct": is_correct})
        graded_answers.append(a)

    return graded_answers, total_score, correct_count


def _simplify_question_snapshot(deployment: ExamDeployment) -> dict[str, dict[str, Any]]:
    return {
        q["id"]: {
            "answer": q["answer"],
            "point": q["point"],
        }
        for q in deployment.questions_snapshot
    }


@transaction.atomic
def create_exam_submission(
    *,
    deployment: ExamDeployment,
    submitter: User,
    started_at: datetime,
    cheating_count: int,
    answers: list[dict[str, Any]],
) -> ExamSubmission:
    """시험 제출 생성 및 자동 채점"""
    graded_answers, total_score, correct_count = grade_answers(deployment, answers)

    submission = ExamSubmission.objects.create(
        submitter=submitter,
        deployment=deployment,
        started_at=started_at,
        cheating_count=cheating_count,
        answers=graded_answers,  # ← 채점 결과 포함된 구조로 저장
        score=total_score,
        correct_answer_count=correct_count,
    )

    return submission
