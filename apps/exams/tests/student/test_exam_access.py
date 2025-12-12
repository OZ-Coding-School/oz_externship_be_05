import datetime
from typing import Any, Dict, List, Optional

from django.test import TestCase
# 시리얼라이저 임포트
from apps.exams.serializers.student.exam_access_serializer import (
    StudentExamAccessSerializer,
)

# 이전에 문제가 되었던 'from .mock_models import ...' 라인은 삭제되었습니다.


# --- 테스트를 위한 가상 모델 정의 ---
class MockExam:
    def __init__(
        self,
        id: int,
        title: str,
        thumbnail_img_url: str,
        subject: Optional[Any],
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.id = id
        self.title = title
        self.thumbnail_img_url = thumbnail_img_url
        self.subject = subject
        self.created_at = created_at if created_at else datetime.datetime.now()


class MockExamDeployment:
    def __init__(
        self,
        id: int,
        exam: MockExam,
        access_code: str,
        duration_time: int,
        open_at: datetime.datetime,
        close_at: datetime.datetime,
        questions_snapshot: List[Dict[str, Any]],
    ) -> None:
        self.id = id
        self.exam = exam
        self.access_code = access_code
        self.duration_time = duration_time
        self.open_at = open_at
        self.close_at = close_at
        self.questions_snapshot = questions_snapshot


# ------------------------------------


class StudentExamAccessSerializerTest(TestCase):

    def setUp(self) -> None:  # -> None 추가 완료
        """테스트에 사용될 가상의 데이터를 준비합니다."""
        mock_exam = MockExam(
            id=1, title="중간고사 시험지 A", thumbnail_img_url="http://example.com/thumb.jpg", subject=None
        )

        self.mock_deployment = MockExamDeployment(
            id=101,
            exam=mock_exam,
            access_code="ABCXYZ123",
            duration_time=90,
            open_at=datetime.datetime(2025, 12, 15, 9, 0, 0),
            close_at=datetime.datetime(2025, 12, 15, 18, 0, 0),
            questions_snapshot=[{"q_id": 1, "content": "문제 1"}],
        )

    def test_serializer_output_correctness(self) -> None:  # -> None 추가 완료
        """시리얼라이저가 배포 정보를 정확히 출력하는지 확인합니다."""
        serializer = StudentExamAccessSerializer(self.mock_deployment)
        data: Any = serializer.data

        self.assertEqual(data["id"], 101)
        self.assertEqual(data["access_code"], "ABCXYZ123")
        self.assertEqual(data["time_limit"], 90)
        self.assertEqual(data["exam_id"], 1)
        self.assertEqual(data["exam_title"], "중간고사 시험지 A")
        self.assertTrue(isinstance(data["questions_snapshot"], list))
