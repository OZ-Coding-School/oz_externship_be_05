from __future__ import annotations

from typing import Any, List, Optional, TypedDict

from apps.exams.models import ExamSubmission


class SnapshotQuestion(TypedDict, total=False):
    # 시험 배포 시점의 문항 스냅샷 구조
    question_id: int
    question: str
    type: str
    prompt: str
    point: int
    options: List[str]
    answer: Any
    explanation: str
    blank_count: Optional[int]


class ResultQuestion(TypedDict):
    # 결과 응답에서 문제 1개에 해당하는 구조
    question_id: int
    number: int
    type: str
    question: str
    prompt: str
    options: list[str]
    point: int
    answer: list[str]
    explanation: str
    submitted_answer: list[str]
    is_correct: bool


def _format_hhmmss(seconds: int) -> str:
    # 초 단위를 "HH:MM:SS" 문자열로 변환
    if seconds < 0:
        seconds = 0

    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60

    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def attach_exam_result_properties(submission: ExamSubmission) -> ExamSubmission:
    # 시험 결과 조회용 응답 데이터 조립
    deployment = submission.deployment

    # 응시 시간 계산 후 submission에 setattr (시작 시각 ~ 제출 시각)
    submitted_at = submission.created_at
    duration_seconds = int((submitted_at - submission.started_at).total_seconds())
    setattr(submission, "elapsed_time", _format_hhmmss(duration_seconds))

    # 시험 배포 시 저장된 문항 스냅샷
    questions_snapshot = deployment.questions_snapshot
    # 사용자가 제출한 답안
    submitted_answers = _simplify_submitted_answers(submission.answers)
    added_questions_snapshot = []

    for question in questions_snapshot:
        question["is_correct"] = submitted_answers[question["id"]]["is_correct"]
        question["submitted_answer"] = submitted_answers[question["id"]]["submitted_answer"]
        added_questions_snapshot.append(question)

    setattr(submission, "result_questions", added_questions_snapshot)

    return submission


def _simplify_submitted_answers(submitted_answers: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    submitted_answers_simplified = {}
    for answer in submitted_answers:
        submitted_answers_simplified[answer["question_id"]] = {
            "is_correct": answer["is_correct"],
            "submitted_answer": answer["submitted_answer"],
        }

    return submitted_answers_simplified
