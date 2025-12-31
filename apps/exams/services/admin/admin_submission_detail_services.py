from typing import Any

from apps.exams.models.exam_submission import ExamSubmission


def calculate_submission_elapsed_time(submission: ExamSubmission) -> int:
    """
    응시에 걸린 시간 계산 (분 단위)
    """
    if not submission or not submission.started_at or not submission.created_at:
        return 0

    return int((submission.created_at - submission.started_at).total_seconds() // 60)


def check_answer_correctness(submitted: Any, correct: Any) -> bool:
    """
    제출한 답안의 정답 여부 확인
    """
    if submitted is None:
        return False

    # 순서 정렬, 다중 선택 등 리스트 비교
    if isinstance(correct, list) and isinstance(submitted, list):
        return bool(submitted == correct)

    # 일반 단일 값 비교
    return bool(submitted == correct)


def normalize_answers(raw_answers: object) -> dict[str, object]:
    """
    ExamSubmission.answers 를 안전하게 dict로 변환
    """
    if raw_answers is None:
        return {}

    if isinstance(raw_answers, dict):
        return raw_answers

    raise ValueError("응시 답안 형식이 올바르지 않습니다.")
