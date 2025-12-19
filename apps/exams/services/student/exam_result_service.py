from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional, TypedDict, cast

from django.utils import timezone


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
    point: int
    options: List[str]
    submitted_answer: Any
    correct_answer: Any
    is_correct: bool
    explanation: str


class ResultResponse(TypedDict):
    # 결과 조회 API의 최상위 응답 구조
    exam_title: str
    thumbnail_img_url: str
    duration: str
    score: int
    total_score: int
    cheating_count: int
    questions: List[ResultQuestion]


def _format_hhmmss(seconds: int) -> str:
    # 초 단위를 문자열로 변환
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=seconds)
    total = int(td.total_seconds())
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def build_exam_result(submission: Any) -> ResultResponse:
    # 시험 결과 조회용 응답 데이터 조립
    deployment = submission.deployment
    exam = deployment.exam

    # 응시 시간 계산 (시작 시각 ~ 제출 시각)
    submitted_at = getattr(submission, "created_at", None) or timezone.now()
    duration_seconds = int((submitted_at - submission.started_at).total_seconds())
    duration_str = _format_hhmmss(duration_seconds)

    # 시험 배포 시 저장된 문항 스냅샷 가져오기
    snapshot_any: Any = getattr(deployment, "questions_snapshot", None)
    questions_snapshot: List[SnapshotQuestion] = []

    if isinstance(snapshot_any, dict):
        raw_list = snapshot_any.get("questions", [])
        if isinstance(raw_list, list):
            questions_snapshot = cast(List[SnapshotQuestion], raw_list)
    elif isinstance(snapshot_any, list):
        questions_snapshot = cast(List[SnapshotQuestion], snapshot_any)

    # 제출한 답안을 question_id → answer 형태로 변환
    answers_any: Any = submission.answers
    answers_map: Dict[int, Any] = {}

    if isinstance(answers_any, dict):
        if "questions" not in answers_any:
            for k, v in answers_any.items():
                try:
                    answers_map[int(k)] = v
                except (TypeError, ValueError):
                    continue
        # 제출 payload 그대로 저장
        else:
            q_list = answers_any.get("questions", [])
            if isinstance(q_list, list):
                for item in q_list:
                    if not isinstance(item, dict):
                        continue
                    qid = item.get("question_id")
                    if qid is None:
                        continue
                    try:
                        answers_map[int(qid)] = item.get("answer")
                    except (TypeError, ValueError):
                        continue

    questions: List[ResultQuestion] = []
    total_score = 0

    # 문항별 결과 조립
    for idx, q in enumerate(questions_snapshot, start=1):
        qid = q.get("question_id")
        if qid is None:
            continue

        point = int(q.get("point") or 0)
        total_score += point

        correct_answer = q.get("answer")
        submitted_answer = answers_map.get(int(qid))

        # 정답 비교
        is_correct = submitted_answer == correct_answer

        questions.append(
            {
                "question_id": int(qid),
                "number": idx,
                "type": str(q.get("type", "")),
                "question": str(q.get("question", "")),
                "prompt": str(q.get("prompt", "") or ""),
                "point": point,
                "options": list(q.get("options", []) or []),
                "submitted_answer": submitted_answer,
                "correct_answer": correct_answer,
                "is_correct": bool(is_correct),
                "explanation": str(q.get("explanation", "") or ""),
            }
        )

    # 시험 기본 정보 + 결과 요약 반환
    thumbnail = getattr(exam, "thumbnail_img_url", "") or ""

    return {
        "exam_title": str(exam.title),
        "thumbnail_img_url": str(thumbnail),
        "duration": duration_str,
        "score": int(submission.score),
        "total_score": int(total_score),
        "cheating_count": int(submission.cheating_count),
        "questions": questions,
    }
