import datetime
from typing import Any, Optional

from django.test import TestCase

# 시리얼라이저 임포트
from apps.exams.serializers.student.exam_list_serializer import ExamListSerializer


# --- 테스트를 위한 가상 모델 정의 ---
class MockSubject:
    def __init__(self, id: int, title: str) -> None:
        self.id = id
        self.title = title


class MockExam:
    def __init__(
        self,
        id: int,
        title: str,
        thumbnail_img_url: str,
        subject: Optional[MockSubject],
        created_at: Optional[datetime.datetime] = None,
    ) -> None:
        self.id = id
        self.title = title
        self.thumbnail_img_url = thumbnail_img_url
        self.subject = subject
        self.created_at = created_at if created_at else datetime.datetime.now()


# ------------------------------------


class ExamListSerializerTest(TestCase):

    def setUp(self) -> None:
        """테스트에 사용될 가상의 데이터를 준비합니다."""
        mock_subject = MockSubject(id=10, title="Python 프로그래밍 기초")

        self.mock_exam = MockExam(
            id=1,
            title="중간고사 시험지 A",
            thumbnail_img_url="http://example.com/thumb.jpg",
            subject=mock_subject,
            created_at=datetime.datetime(2025, 12, 12, 10, 0, 0),
        )

    def test_serializer_output_correctness(self) -> None:
        """시리얼라이저가 시험 목록 데이터를 정확히 출력하는지 확인합니다."""
        serializer = ExamListSerializer(self.mock_exam)
        data: Any = serializer.data

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "중간고사 시험지 A")
        self.assertEqual(data["subject_title"], "Python 프로그래밍 기초")
        self.assertIn("created_at", data)
