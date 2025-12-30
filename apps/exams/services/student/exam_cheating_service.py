from typing import Any

from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission

MAX_CHEATING_COUNT = 3


def handle_cheating_event(submission: ExamSubmission, deployment: ExamDeployment) -> dict[str, Any]:
    """
    부정행위 이벤트 처리 메인 로직
    """

    # 부정행위 카운트 증가
    submission.cheating_count += 1
    is_forced_submitted = False

    # 3회 적발 시 강제 제출
    if submission.cheating_count >= MAX_CHEATING_COUNT:
        is_forced_submitted = True
        _force_submit_exam(submission, deployment)

    submission.save()

    return {
        "cheating_count": submission.cheating_count,
        "is_forced_submitted": is_forced_submitted,
    }


def _force_submit_exam(submission: ExamSubmission, deployment: ExamDeployment) -> None:
    """
    부정행위 3회 적발 시 강제 제출 처리
    - 현재까지 푼 문제까지만 저장하고 나머지 문항은 빈 답안으로 채우고 자동 채점
    """

    questions_snapshot = deployment.questions_snapshot
    current_answers = submission.answers if submission.answers else {}

    # 모든 문제에 대해 답안 확인, 없으면 빈 답안 처리
    complete_answers = _fill_empty_answers(questions_snapshot, current_answers)

    # 답안 저장 및 채점
    submission.answers = complete_answers
    score, correct_count = _calculate_score(questions_snapshot, complete_answers)
    submission.score = score
    submission.correct_answer_count = correct_count


def _fill_empty_answers(questions: list[dict[str, Any]], current_answers: dict[str, Any]) -> dict[str, Any]:
    """
    풀지 않은 문항을 빈 답안으로 채움
    """
    complete_answers = current_answers.copy()

    for question in questions:
        question_id = str(question["id"])
        if question_id not in complete_answers:
            # 문제 유형에 따라 빈 답안 형식 설정
            question_type = question["type"]
            complete_answers[question_id] = _get_empty_answer(question_type, question.get("blank_count", 1))

    return complete_answers


def _get_empty_answer(question_type: str, blank_count: int = 1) -> Any:
    """
    문제 유형별 빈 답안 반환
    """
    if question_type == "fill_blank":
        return [""] * blank_count
    elif question_type in ["multiple_choice", "ordering"]:
        return []
    else:
        return ""


def _calculate_score(questions: list[dict[str, Any]], answers: dict[str, Any]) -> tuple[int, int]:
    """
    답안 채점 로직
    """
    total_score = 0
    correct_count = 0

    for question in questions:
        question_id = str(question["id"])
        user_answer = answers.get(question_id)
        correct_answer = question["answer"]

        if _is_correct_answer(user_answer, correct_answer, question["type"]):
            total_score += question["point"]
            correct_count += 1

    return total_score, correct_count


def _is_correct_answer(user_answer: Any, correct_answer: Any, question_type: str) -> bool:
    """
    문제 유형별 정답 여부 판단
    """
    if user_answer is None or user_answer == "" or user_answer == []:
        return False

    if question_type in ["multiple_choice", "ordering", "fill_blank"]:
        if not isinstance(user_answer, list) or not isinstance(correct_answer, list):
            return False
        return user_answer == correct_answer

    # 단일 선택, OX, 단답형은 문자열 비교
    return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
