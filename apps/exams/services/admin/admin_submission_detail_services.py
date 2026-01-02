from typing import Any

from apps.exams.models import ExamSubmission


def get_merged_submission_detail(submission: ExamSubmission) -> ExamSubmission:
    """
    Submission 객체에 시험 Snapshot 데이터를 병합
    """
    # 제출 답안 dict로 맵핑 (id를 키로 사용)
    answers_map = {str(a["id"]): a for a in submission.answers}

    # 시험 문항 스냅샷 가져오기
    snapshot = submission.deployment.questions_snapshot

    merged_questions: list[dict[str, Any]] = []

    # 스냅샷 기준으로 루프를 돌며 병합
    for idx, q in enumerate(snapshot, start=1):
        q_id = str(q["id"])
        answer_data = answers_map.get(q_id, {})

        merged_questions.append(
            {
                **q,
                "number": idx,  # 문제 번호 (1부터 시작)
                "submitted_answer": answer_data.get("submitted_answer"),
                "is_correct": answer_data.get("is_correct", False),
            }
        )

    # Serializer에서 source="merged_questions"로 쓸거임
    setattr(submission, "merged_questions", merged_questions)

    return submission
