from datetime import date, datetime, timedelta
from typing import Any

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models.exam import Exam
from apps.exams.models.exam_deployment import ExamDeployment
from apps.exams.models.exam_question import ExamQuestion, QuestionType
from apps.exams.models.exam_submission import ExamSubmission
from apps.exams.serializers.student.exam_submit_serializer import (
    ExamSubmissionCreateSerializer,
)
from apps.exams.services.student.exam_submit_service import (
    create_exam_submission,
    evaluate_submission,
    normalize_answers,
)
from apps.user.models import User
from apps.user.models.user import RoleChoices


class ExamSubmitServiceAndSerializerTest(APITestCase):
    # service / serializer 유닛 테스트
    deployment: ExamDeployment

    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="service@test.com",
            name="서비스테스트",
            password="1234",
            birthday=date(2000, 1, 1),
            role=RoleChoices.ST,
        )

        # 코스 생성
        self.course = Course.objects.create(
            name="course",
            tag="TT",
            description="test course description",
        )

        # 코호트 생성
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

        # 과목 생성
        self.subject = Subject.objects.create(
            course=self.course,
            title="service subject",
            number_of_days=1,
            number_of_hours=1,
        )

        # 시험 생성
        self.exam = Exam.objects.create(
            title="service exam",
            subject=self.subject,
        )

        # 문제 세트

        # SINGLE_CHOICE
        self.single_choice_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 아침에 일어나면 가장 먼저 하는 행동은 무엇인가요?",
            explanation="테스트용 설명",
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

        # MULTIPLE_CHOICE
        self.multiple_choice_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 하루 동안 반드시 지켜야 하는 두 가지 규칙은 무엇인가요?",
            explanation="테스트용 설명",
            type=QuestionType.MULTIPLE_CHOICE,
            options=[
                "감사 인사하기",
                "간식 몰래 먹기",
                "화내지 않기",
                "주변 사람에게 칭찬하기",
            ],
            answer=["1", "4"],
            point=10,
        )

        # OX
        self.ox_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주는 힘든 일이 있어도 원망하거나 투덜대지 않는다. (O/X)",
            explanation="테스트용 설명",
            type=QuestionType.OX,
            answer="O",
            point=3,
        )

        # SHORT_ANSWER
        self.short_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 규칙 1번은 무엇인가요?",
            explanation="테스트용 설명",
            type=QuestionType.SHORT_ANSWER,
            answer="울지않기",
            point=5,
        )

        # ORDERING
        self.ordering_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 아침 준비 루틴을 순서대로 나열하세요.",
            explanation="테스트용 설명",
            type=QuestionType.ORDERING,
            options=[
                "A: 침대 정리",
                "B: 창문 열기",
                "C: 미소 지으며 인사하기",
                "D: 따뜻한 차 마시기",
            ],
            answer=["A", "B", "C", "D"],
            point=7,
        )

        # FILL_BLANK
        self.fill_blank_question = ExamQuestion.objects.create(
            exam=self.exam,
            question='공주의 좌우명을 완성하세요: "_____, 그리고 _____."',
            explanation="테스트용 설명",
            type=QuestionType.FILL_BLANK,
            blank_count=2,
            answer=["용기", "친절"],
            point=8,
        )

        # 시험 배포 생성
        questions = [
            self.single_choice_question,
            self.multiple_choice_question,
            self.ox_question,
            self.short_question,
            self.ordering_question,
            self.fill_blank_question,
        ]

        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=60,
            open_at=timezone.now(),
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
                    for q in questions
                ]
            },
        )

        # RequestFactory 는 serializer 의 context["request"] 에 넣어주기 위해 사용
        self.rf = RequestFactory()

        self.client.force_authenticate(user=self.user)

    # -------------------- service 테스트 --------------------

    def test_normalize_answers_fills_all_questions(self) -> None:
        # normalize_answers 가 exam.questions 전체 id 를 키로 가진 dict 를 만들어주는지 확인
        # 일부 문항만 답을 보내도, 나머지는 None 으로 채워져야 한다.
        raw_answers = [{"question_id": self.single_choice_question.id, "answer": "3"}]

        normalized = normalize_answers(deployment=self.deployment, raw_answers=raw_answers)

        self.assertEqual(normalized[self.single_choice_question.id], "3")
        # 안 보낸 것 → None 이어야 함
        self.assertIsNone(normalized[self.multiple_choice_question.id])
        self.assertIsNone(normalized[self.ox_question.id])

    def test_evaluate_submission_all_correct(self) -> None:
        # evaluate_submission 이 각 QuestionType 에 대해 정답 판별을 올바르게 하는지 확인
        normalized: dict[int, Any] = {
            self.single_choice_question.id: "3",
            self.multiple_choice_question.id: ["1", "4"],
            self.ox_question.id: "O",
            self.short_question.id: "울지않기",
            self.ordering_question.id: ["A", "B", "C", "D"],
            self.fill_blank_question.id: ["용기", "친절"],
        }

        total_score, correct_count = evaluate_submission(deployment=self.deployment, normalized_answers=normalized)

        self.assertEqual(total_score, 38)
        self.assertEqual(correct_count, 6)

    def test_create_exam_submission(self) -> None:
        # create_exam_submission 이 실제 ExamSubmission 을 생성하고
        # score / correct_answer_count 를 올바르게 저장하는지 확인
        # 'answers' 대신 'questions' 키를 사용하거나 리스트로 전달
        raw_answers = [{"question_id": self.single_choice_question.id, "answer": "3"}]

        submission = create_exam_submission(
            deployment=self.deployment,
            submitter=self.user,
            started_at=timezone.now() - timedelta(seconds=5),
            cheating_count=1,
            raw_answers=raw_answers,
        )

        self.assertIsInstance(submission, ExamSubmission)
        self.assertEqual(submission.submitter, self.user)
        self.assertEqual(submission.deployment, self.deployment)
        self.assertEqual(submission.correct_answer_count, 1)
        self.assertEqual(submission.score, self.single_choice_question.point)

    # -------------------- serializer 테스트 --------------------

    def _make_serializer(self, data: dict[str, Any]) -> ExamSubmissionCreateSerializer:
        # ExamSubmissionCreateSerializer 를 테스트하기 위해
        # fake request + context(submission) 를 만들어주는 helper 메서드
        req = self.rf.post("/fake-url/", data, content_type="application/json")
        req.user = self.user
        return ExamSubmissionCreateSerializer(
            data=data,
            context={"request": req, "deployment": self.deployment},
        )

    def test_serializer_validate_and_create_success(self) -> None:
        # 정상 payload 는 is_valid() + save() 까지 통과해야 한다.
        payload: dict[str, Any] = {
            "submitter_id": self.user.id,
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": [],
        }

        serializer = self._make_serializer(payload)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        # serializer.save() 호출 시 context와 validated_data로 create_exam_submission 호출
        submission = serializer.save()
        self.assertIsInstance(submission, ExamSubmission)
        self.assertEqual(submission.submitter, self.user)
        self.assertEqual(submission.deployment, self.deployment)
        self.assertEqual(submission.correct_answer_count, 0)
        self.assertEqual(submission.score, 0)


class ExamSubmissionViewTest(APITestCase):
    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="service@test.com",
            name="서비스테스트",
            password="1234",
            birthday=date(2000, 1, 1),
            role=RoleChoices.ST,
        )

        # 코스 생성
        self.course = Course.objects.create(
            name="course",
            tag="TT",
            description="test course description",
        )

        # 코호트 생성
        self.cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=20,
            start_date=timezone.make_aware(datetime(2025, 1, 1)),
            end_date=timezone.make_aware(datetime(2025, 2, 1)),
        )

        # 과목 생성
        self.subject = Subject.objects.create(
            course=self.course,
            title="service subject",
            number_of_days=1,
            number_of_hours=1,
        )

        # 시험 생성
        self.exam = Exam.objects.create(
            title="service exam",
            subject=self.subject,
        )

        # 문제 세트

        # SINGLE_CHOICE
        self.single_choice_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주가 아침에 일어나면 가장 먼저 하는 행동은 무엇인가요?",
            explanation="테스트용 설명",
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

        # 시험 배포 생성
        self.deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=60,
            open_at=timezone.now(),
            close_at=timezone.now() + timedelta(hours=1),
            questions_snapshot={
                "questions": [
                    {
                        "question_id": self.single_choice_question.id,
                        "question": self.single_choice_question.question,
                        "type": self.single_choice_question.type,
                        "answer": self.single_choice_question.answer,
                        "point": self.single_choice_question.point,
                    }
                ]
            },
        )

        self.client.force_authenticate(user=self.user)

    def test_exam_submission_view(self) -> None:
        url = reverse("exam_submit")

        data = {
            "deployment_id": self.deployment.id,
            "submitter_id": self.user.id,
            "started_at": (timezone.now() - timedelta(minutes=5)).isoformat(),
            "cheating_count": 1,
            "answers": [
                {"question_id": self.single_choice_question.id, "type": "single_choice", "submitted_answer": "3"}
            ],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
