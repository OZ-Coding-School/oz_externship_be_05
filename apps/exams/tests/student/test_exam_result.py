from datetime import date, datetime, timedelta
from typing import Any

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models.exam import Exam
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import ExamQuestion, QuestionType
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.services.student.exam_submit_service import create_exam_submission
from apps.user.models import User
from apps.user.models.user import RoleChoices


class ExamSubmissionResultViewTest(APITestCase):
    def setUp(self) -> None:
        # 테스트용 사용자
        self.user = User.objects.create_user(
            email="owner@test.com", name="응시자", password="1234", birthday=date(2000, 1, 1), role=RoleChoices.ST
        )
        self.other = User.objects.create_user(
            email="other@test.com", name="다른사람", password="1234", birthday=date(2000, 1, 1), role=RoleChoices.ST
        )

        # 시험 기본 구조
        self.course = Course.objects.create(
            name="course",
            tag="TT",
            description="test course description",
        )
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )
        self.subject = Subject.objects.create(
            course=self.course,
            title="service subject",
            number_of_days=1,
            number_of_hours=1,
        )
        self.exam = Exam.objects.create(
            title="공주의 조건 테스트",
            subject=self.subject,
        )

        # 문항 2개 정답/오답 확인
        self.q1 = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 아침에 일어나면 가장 먼저 하는 행동은 무엇인가요?",
            explanation="공주는 미소로 하루를 시작합니다.",
            type=QuestionType.SINGLE_CHOICE,
            options=[
                "기지개 켜기",
                "창문 열고 햇빛 맞기",
                "미소 지으며 '좋은 아침!' 말하기",
                "왕궁 산책 나가기",
            ],
            answer="3",
            point=5,
        )
        self.q2 = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 규칙 1번은 무엇인가요?",
            explanation="공주의 첫 번째 규칙은 '울지않기'입니다.",
            type=QuestionType.SHORT_ANSWER,
            answer="울지않기",
            point=7,
        )

        # 시험 배포 결과 snapshot 기준
        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=60,
            open_at=timezone.now() - timedelta(minutes=10),
            close_at=timezone.now() + timedelta(hours=1),
            questions_snapshot={
                "questions": [
                    {
                        "question_id": q.id,
                        "question": q.question,
                        "type": q.type,
                        "prompt": getattr(q, "prompt", "") or "",
                        "point": q.point,
                        "options": getattr(q, "options", []) or [],
                        "answer": q.answer,
                        "explanation": q.explanation,
                        "blank_count": getattr(q, "blank_count", None),
                    }
                    for q in [self.q1, self.q2]
                ]
            },
        )

        # 제출 결과 생성
        raw_answers: dict[str, Any] = {
            "questions": [
                {"question_id": self.q1.id, "answer": "3"},
                {"question_id": self.q2.id, "answer": "아무말"},
            ]
        }

        self.submission = create_exam_submission(
            deployment=self.deployment,
            submitter=self.user,
            started_at=timezone.now() - timedelta(seconds=30),
            cheating_count=1,
            raw_answers=raw_answers,
        )

        self.client.force_authenticate(user=self.user)

    def test_result_success_200(self) -> None:
        # 본인 제출 결과 정상 조회
        url = reverse("exam_result", kwargs={"submission_id": self.submission.id})

        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        data = res.data

        self.assertEqual(data["exam_title"], self.exam.title)
        self.assertEqual(data["cheating_count"], self.submission.cheating_count)
        self.assertEqual(data["total_score"], self.q1.point + self.q2.point)

        self.assertEqual(len(data["questions"]), 2)

        q1_res, q2_res = data["questions"]

        self.assertEqual(q1_res["submitted_answer"], "3")
        self.assertTrue(q1_res["is_correct"])

        self.assertEqual(q2_res["submitted_answer"], "아무말")
        self.assertFalse(q2_res["is_correct"])

    def test_result_forbidden_403(self) -> None:
        # 타인의 제출 결과 접근 차단
        url = reverse("exam_result", kwargs={"submission_id": self.submission.id})
        self.client.force_authenticate(user=self.other)

        res = self.client.get(url)
        self.assertEqual(res.status_code, 403)

    def test_result_not_found_404(self) -> None:
        # 존재하지 않는 submission_id
        url = reverse("exam_result", kwargs={"submission_id": 99999999})

        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

    def test_result_unauthorized_401(self) -> None:
        # 인증 없이 접근
        self.client.force_authenticate(user=None)
        url = reverse("exam_result", kwargs={"submission_id": self.submission.id})

        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

    def test_result_invalid_session_400(self) -> None:
        # started_at > created_at 인 비정상 세션
        invalid_submission = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.user,
            started_at=timezone.now(),
            created_at=timezone.now() - timedelta(seconds=10),
            cheating_count=0,
            answers=[],
            score=0,
            correct_answer_count=0,
        )

        # auto_now_add를 우회하기 위해 update 사용
        ExamSubmission.objects.filter(id=invalid_submission.id).update(created_at=timezone.now() - timedelta(days=1))

        url = reverse("exam_result", kwargs={"submission_id": invalid_submission.id})

        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)
