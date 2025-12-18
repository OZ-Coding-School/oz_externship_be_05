from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class DeploymentListItemDTO:
    """배포 목록 아이템"""

    deployment_id: int
    exam_title: str
    subject_name: str
    cohort_number: int
    course_name: str
    submit_count: int
    avg_score: float
    status: str
    created_at: datetime


@dataclass
class QuestionSnapshotDTO:
    """문항 스냅샷"""

    question_id: int
    type: str
    question: str
    point: int


@dataclass
class DeploymentDetailDTO:
    """배포 상세 정보"""

    # Exam 정보
    exam_id: int
    exam_title: str
    subject_name: str
    questions: List[QuestionSnapshotDTO]

    # Deployment 정보
    deployment_id: int
    access_code: str
    course_name: str
    cohort_number: int
    submit_count: int
    not_submitted_count: int
    duration_time: int
    open_at: datetime
    close_at: datetime
    created_at: datetime
