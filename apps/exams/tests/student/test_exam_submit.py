import json
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


class ExamSubmitServiceAndSerializerTest(TestCase):
    # service / serializer 유닛 테스트
    deployment: ExamDeployment

    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="service@test.com",
            name="서비스테스트",
            password="1234",
            birthday=date(2000, 1, 1),
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
            type=QuestionType.OX,
            answer="O",
            point=3,
        )

        # SHORT_ANSWER
        self.short_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 규칙 1번은 무엇인가요?",
            type=QuestionType.SHORT_ANSWER,
            answer="울지않기",
            point=5,
        )

        # ORDERING
        self.ordering_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 아침 준비 루틴을 순서대로 나열하세요.",
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
                        "answer": q.answer,
                        "point": q.point,
                    }
                    for q in questions
                ]
            },
        )

        # RequestFactory 는 serializer 의 context["request"] 에 넣어주기 위해 사용
        self.rf = RequestFactory()

    # -------------------- service 테스트 --------------------

    def test_normalize_answers_fills_all_questions(self) -> None:
        # normalize_answers 가 exam.questions 전체 id 를 키로 가진 dict 를 만들어주는지 확인
        # 일부 문항만 답을 보내도, 나머지는 None 으로 채워져야 한다.
        raw_answers: dict[str, Any] = {
            "questions": [
                {"question_id": self.single_choice_question.id, "answer": "3"},
            ]
        }

        normalized = normalize_answers(self.deployment, raw_answers)

        # 모든 문제 id 가 key 로 들어있는지 확인
        question_ids = list(self.exam.questions.values_list("id", flat=True))
        self.assertEqual(sorted(normalized.keys()), sorted(question_ids))

        # 보낸 것 → 값 채워짐
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

        total_score, correct_count = evaluate_submission(self.deployment, normalized)

        self.assertEqual(total_score, 38)
        self.assertEqual(correct_count, 6)

    def test_create_exam_submission(self) -> None:
        # create_exam_submission 이 실제 ExamSubmission 을 생성하고
        # score / correct_answer_count 를 올바르게 저장하는지 확인
        raw_answers: dict[str, Any] = {
            "questions": [
                {"question_id": self.short_question.id, "answer": "울지않기"},
            ]
        }

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
        self.assertEqual(submission.score, self.short_question.point)

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
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {"questions": []},
        }

        serializer = self._make_serializer(payload)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        submission = serializer.save(submitter=self.user, submission=self.deployment)
        self.assertIsInstance(submission, ExamSubmission)

    def test_serializer_block_third_submission(self) -> None:
        # 같은 유저 / 같은 submission 에 대해
        # 2회까지는 통과, 3회차에서 ValidationError 가 발생해야 한다.
        payload: dict[str, Any] = {
            "started_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            "cheating_count": 0,
            "answers": {"questions": []},
        }

        # 1회차
        s1 = self._make_serializer(payload)
        self.assertTrue(s1.is_valid(), msg=s1.errors)
        s1.save(submitter=self.user, submission=self.deployment)

        # 2회차
        s2 = self._make_serializer(payload)
        self.assertTrue(s2.is_valid(), msg=s2.errors)
        s2.save(submitter=self.user, submission=self.deployment)

        # 3회차 → 실패해야 함
        s3 = self._make_serializer(payload)
        self.assertFalse(s3.is_valid())
        self.assertIn("이미 제출된 시험입니다.", str(s3.errors))

    def test_serializer_missing_started_at(self) -> None:
        # started_at 필드가 누락된 경우 에러가 발생해야 한다.
        payload: dict[str, Any] = {
            # "started_at" 없음
            "cheating_count": 0,
            "answers": {"questions": []},
        }

        serializer = self._make_serializer(payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("started_at", serializer.errors)

    def test_serializer_future_started_at(self) -> None:
        # started_at 이 미래 시각이면 에러
        payload: dict[str, Any] = {
            "started_at": (timezone.now() + timedelta(seconds=30)).isoformat(),
            "cheating_count": 0,
            "answers": {"questions": []},
        }

        serializer = self._make_serializer(payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("시작시간은 현재 시간보다 빨라야합니다.", str(serializer.errors))

    def test_serializer_time_over_flag(self) -> None:
        payload: dict[str, Any] = {
            "started_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
            "cheating_count": 0,
            "answers": {"questions": []},
        }

        serializer = self._make_serializer(payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("시험 제한 시간이 초과되어 자동제출되었습니다", str(serializer.errors))

    def test_serializer_to_representation(self) -> None:
        # to_representation 이 채점 결과 페이지에 필요한 필드를 모두 포함하는지 확인
        raw_answers: dict[str, Any] = {
            "questions": [
                {"question_id": self.short_question.id, "answer": "울지않기"},
            ]
        }

        submission = create_exam_submission(
            deployment=self.deployment,
            submitter=self.user,
            started_at=timezone.now() - timedelta(seconds=5),
            cheating_count=2,
            raw_answers=raw_answers,
        )

        serializer = ExamSubmissionCreateSerializer()
        data = serializer.to_representation(submission)

        self.assertEqual(data["id"], submission.pk)
        self.assertEqual(data["submission_id"], self.deployment.pk)


class ExamSubmissionViewTest(APITestCase):
    def setUp(self) -> None:
        # 유저 생성
        self.user = User.objects.create_user(
            email="service@test.com",
            name="서비스테스트",
            password="1234",
            birthday=date(2000, 1, 1),
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
            type=QuestionType.OX,
            answer="O",
            point=3,
        )

        # SHORT_ANSWER
        self.short_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 규칙 1번은 무엇인가요?",
            type=QuestionType.SHORT_ANSWER,
            answer="울지않기",
            point=5,
        )

        # ORDERING
        self.ordering_question = ExamQuestion.objects.create(
            exam=self.exam,
            question="공주의 아침 준비 루틴을 순서대로 나열하세요.",
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
                        "answer": q.answer,
                        "point": q.point,
                    }
                    for q in questions
                ]
            },
        )

    def test_exam_submission_view(self) -> None:
        url = reverse("exam_submit")
        self.client.force_authenticate(user=self.user)
        data = {
            "started_at": (timezone.now() - timedelta(minutes=50)).isoformat(),
            "cheating_count": 1,
            "answers": {"questions": [{"question_id": self.single_choice_question.id, "answer": "3"}]},
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 400)
