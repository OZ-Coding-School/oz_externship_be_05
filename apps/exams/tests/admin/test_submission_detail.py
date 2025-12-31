from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_submission import ExamSubmission
from apps.user.models.user import GenderChoices, User


class ExamAdminSubmissionDetailViewTestCase(APITestCase):

    admin_user: User
    student_user: User
    unauthorized_user: User
    course: Course
    subject: Subject
    cohort: Cohort
    exam: Exam
    deployment: ExamDeployment
    submission: ExamSubmission

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 데이터 설정"""
        # Users
        cls.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            password="password123",
            name="관리자",
            phone_number="010-1234-5678",
            gender=GenderChoices.MALE,
            birthday=date.today() - timedelta(days=10000),
        )

        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="password123",
            name="학생",
            phone_number="010-2345-6789",
            gender=GenderChoices.FEMALE,
            birthday=date.today() - timedelta(days=8000),
        )

        cls.unauthorized_user = User.objects.create_user(
            email="user@test.com",
            password="password123",
            name="일반유저",
            phone_number="010-3456-7890",
            gender=GenderChoices.MALE,
            birthday=date.today() - timedelta(days=9000),
        )

        # Course / Subject / Cohort / Exam / Deployment
        cls.course = Course.objects.create(name="테스트")
        cls.subject = Subject.objects.create(
            title="나",
            course=cls.course,
            number_of_days=10,
            number_of_hours=20,
        )
        cls.cohort = Cohort.objects.create(
            number=1,
            course=cls.course,
            max_student=30,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        cls.exam = Exam.objects.create(
            subject=cls.subject,
            title="중간고사",
        )

        now = timezone.now()
        cls.deployment = ExamDeployment.objects.create(
            exam=cls.exam,
            cohort=cls.cohort,
            duration_time=60,
            open_at=now - timedelta(hours=2),
            close_at=now + timedelta(hours=2),
            questions_snapshot=[
                {
                    "question_id": 1,
                    "type": "multiple_choice",
                    "question": "다음 중 지금 내 심정을 모두 고르시오",
                    "prompt": None,
                    "options": ["햎삐", "아자스", "화나쓰", "멍~"],
                    "answer": "멍~",
                    "point": 10,
                    "explanation": "잠을 못 자서 머리가 멍해요",
                },
                {
                    "question_id": 2,
                    "type": "multiple_choice",
                    "question": "곧 있을 휴가 날짜를 맞춰보세요",
                    "prompt": None,
                    "options": ["12/31", "1/2", "1/5", "1/6"],
                    "answer": ["12/31", "1/2"],
                    "point": 15,
                    "explanation": "연말과 연초 모두 쉬는 마법",
                },
                {
                    "question_id": 3,
                    "type": "short_answer",
                    "question": "내가 좋아하는 숫자는?",
                    "prompt": "0 이상의 정수 중에 있습니다.",
                    "options": None,
                    "answer": "0",
                    "point": 20,
                    "explanation": "0이 숫자 뒤에 붙으면 자릿수가 계속 커진닿 ㅔ헤",
                },
            ],
        )

        # ExamSubmission
        cls.submission = ExamSubmission.objects.create(
            deployment=cls.deployment,
            submitter=cls.student_user,
            started_at=now - timedelta(minutes=30),
            created_at=now,
            answers={
                "1": "멍~",
                "2": ["12/31", "1/2"],
                "3": "0",
            },
            score=45,
            correct_answer_count=3,
            cheating_count=0,
        )

    def _get_detail_url(self, submission_id: int) -> str:
        return reverse("exam_submission_detail", kwargs={"submission_id": submission_id})

    def test_get_submission_detail_success(self) -> None:
        """
        응시 내역 상세 조회 성공 및 기본 응답 구조 확인
        """
        self.client.force_authenticate(user=self.admin_user)

        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 최상위 구조 검증
        self.assertIn("exam", response.data)
        self.assertIn("student", response.data)
        self.assertIn("result", response.data)
        self.assertIn("questions", response.data)

        # 시험 정보 검증
        exam_data = response.data["exam"]
        self.assertEqual(exam_data["exam_title"], "중간고사")
        self.assertEqual(exam_data["subject_name"], "나")
        self.assertEqual(exam_data["duration_time"], 60)
        self.assertIn("open_at", exam_data)
        self.assertIn("close_at", exam_data)

        # 학생 정보 검증
        student_data = response.data["student"]
        self.assertEqual(student_data["name"], "학생")
        self.assertEqual(student_data["course_name"], "테스트")
        self.assertEqual(student_data["cohort_number"], 1)

        # 결과 정보 검증
        result_data = response.data["result"]
        self.assertEqual(result_data["score"], 45)
        self.assertEqual(result_data["correct_answer_count"], 3)
        self.assertEqual(result_data["total_question_count"], 3)
        self.assertEqual(result_data["cheating_count"], 0)
        self.assertEqual(result_data["elapsed_time"], 30)

        # 문제 정보 검증
        self.assertEqual(len(response.data["questions"]), 3)

    def test_get_submission_detail_questions_structure(self) -> None:
        """
        문제별 상세 데이터 구조 검증
        """
        self.client.force_authenticate(user=self.admin_user)

        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        questions = response.data["questions"]

        # 첫 번째 문제 (객관식) 구조 검증
        q1 = questions[0]
        self.assertEqual(q1["question_id"], 1)
        self.assertEqual(q1["number"], 1)
        self.assertEqual(q1["type"], "multiple_choice")
        self.assertIn("question", q1)
        self.assertIn("options", q1)
        self.assertEqual(q1["point"], 10)
        self.assertIn("submitted_answer", q1)
        self.assertIn("correct_answer", q1)
        self.assertIn("is_correct", q1)
        self.assertIn("explanation", q1)

        # 두 번째 문제 (다중 선택) 구조 검증
        q2 = questions[1]
        self.assertEqual(q2["type"], "multiple_choice")
        self.assertIsInstance(q2["submitted_answer"], list)
        self.assertIsInstance(q2["correct_answer"], list)

        # 세 번째 문제 (주관식) 구조 검증
        q3 = questions[2]
        self.assertEqual(q3["type"], "short_answer")
        self.assertIsNotNone(q3["prompt"])
        self.assertIsNone(q3["options"])

    def test_get_submission_detail_all_correct_answers(self) -> None:
        """
        모든 정답 제출 시 is_correct 검증
        """
        self.client.force_authenticate(user=self.admin_user)

        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        questions = response.data["questions"]

        # 모든 문제 정답 확인
        for question in questions:
            self.assertTrue(question["is_correct"])
            self.assertEqual(
                question["submitted_answer"],
                question["correct_answer"],
            )

    def test_get_submission_detail_with_wrong_answers(self) -> None:
        """
        오답 포함 응시 내역 조회
        """
        wrong_submission = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=60),
            created_at=timezone.now() - timedelta(minutes=30),
            answers={
                "1": "아자스",  # 오답
                "2": ["1/2"],  # 부분 오답
                "3": None,  # 미제출
            },
            score=0,
            correct_answer_count=0,
            cheating_count=1,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(wrong_submission.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        questions = response.data["questions"]

        # 첫 번째 문제 - 오답
        self.assertEqual(questions[0]["submitted_answer"], "아자스")
        self.assertFalse(questions[0]["is_correct"])

        # 두 번째 문제 - 부분 오답
        self.assertEqual(questions[1]["submitted_answer"], ["1/2"])
        self.assertFalse(questions[1]["is_correct"])

        # 세 번째 문제 - 미제출
        self.assertIsNone(questions[2]["submitted_answer"])
        self.assertFalse(questions[2]["is_correct"])

        # 결과 정보
        self.assertEqual(response.data["result"]["score"], 0)
        self.assertEqual(response.data["result"]["correct_answer_count"], 0)
        self.assertEqual(response.data["result"]["cheating_count"], 1)

    def test_get_submission_detail_not_found(self) -> None:
        """
        존재하지 않는 응시 내역 조회 시 404 확인
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(999999)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("응시 내역", str(response.data))

    def test_get_submission_detail_unauthorized(self) -> None:
        """
        인증되지 않은 사용자의 접근 시 401 확인
        """
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_submission_detail_forbidden(self) -> None:
        """
        권한 없는 사용자의 접근 시 403 확인
        """
        self.client.force_authenticate(user=self.unauthorized_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_elapsed_time_calculation_exact_30_minutes(self) -> None:
        """
        정확히 30분 소요 시간 계산 검증
        """
        submission_30min = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=30),
            created_at=timezone.now(),
            answers={"1": "멍~"},
            score=10,
            correct_answer_count=1,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission_30min.id)
        response = self.client.get(url)

        self.assertEqual(response.data["result"]["elapsed_time"], 30)

    def test_elapsed_time_with_seconds_truncated(self) -> None:
        """
        초 단위 소요 시간이 분으로 내림 처리되는지 검증
        """

        submission = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=25, seconds=59),
            created_at=timezone.now(),
            answers={"1": "멍~"},
            score=10,
            correct_answer_count=1,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission.id)
        response = self.client.get(url)

        # 25분 59초 -> 25분으로 내림
        self.assertEqual(response.data["result"]["elapsed_time"], 25)

    def test_question_ordering_preserved(self) -> None:
        """
        문제 순서가 올바르게 유지되는지 검증
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        questions = response.data["questions"]

        # number가 1, 2, 3 순서로 되어있는지 확인
        for idx, question in enumerate(questions, start=1):
            self.assertEqual(question["number"], idx)

    def test_datetime_format_validation(self) -> None:
        """
        날짜 시간 포맷 검증 (YYYY-MM-DD HH:MM:SS)
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        open_at = response.data["exam"]["open_at"]
        close_at = response.data["exam"]["close_at"]

        # YYYY-MM-DD HH:MM:SS 형식 검증
        self.assertRegex(open_at, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertRegex(close_at, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_multiple_choice_answer_correctness(self) -> None:
        """
        객관식 답안 정답 판정 로직 검증
        """

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        q1 = response.data["questions"][0]
        self.assertEqual(q1["type"], "multiple_choice")
        self.assertEqual(q1["submitted_answer"], "멍~")
        self.assertEqual(q1["correct_answer"], "멍~")
        self.assertTrue(q1["is_correct"])

    def test_multiple_select_answer_correctness(self) -> None:
        """
        다중 선택 답안 정답 판정 로직 검증
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        q2 = response.data["questions"][1]
        self.assertEqual(q2["type"], "multiple_choice")
        self.assertEqual(q2["submitted_answer"], ["12/31", "1/2"])
        self.assertEqual(q2["correct_answer"], ["12/31", "1/2"])
        self.assertTrue(q2["is_correct"])

    def test_short_answer_correctness(self) -> None:
        """
        주관식 답안 정답 판정 로직 검증
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        q3 = response.data["questions"][2]
        self.assertEqual(q3["type"], "short_answer")
        self.assertEqual(q3["submitted_answer"], "0")
        self.assertEqual(q3["correct_answer"], "0")
        self.assertTrue(q3["is_correct"])

    def test_null_submitted_answer_marked_incorrect(self) -> None:
        """
        미제출 답안은 오답 처리되는지 검증
        """
        submission_with_null = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=30),
            created_at=timezone.now(),
            answers={"1": None, "2": None, "3": None},
            score=0,
            correct_answer_count=0,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission_with_null.id)
        response = self.client.get(url)

        questions = response.data["questions"]

        for question in questions:
            self.assertIsNone(question["submitted_answer"])
            self.assertFalse(question["is_correct"])

    def test_total_question_count_matches_snapshot(self) -> None:
        """
        전체 문제 수가 questions_snapshot과 일치하는지 검증
        """
        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(self.submission.id)
        response = self.client.get(url)

        total_count = response.data["result"]["total_question_count"]
        questions_count = len(response.data["questions"])
        snapshot_count = len(self.deployment.questions_snapshot)

        self.assertEqual(total_count, questions_count)
        self.assertEqual(total_count, snapshot_count)

    def test_get_submission_detail_with_invalid_answers_format(self) -> None:
        """
        잘못된 answers 형식(dict가 아닌 경우) 조회 시 400 확인
        """
        # answers가 문자열인 경우
        submission_invalid_str = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=30),
            created_at=timezone.now(),
            answers="invalid_string",  # type: ignore
            score=0,
            correct_answer_count=0,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission_invalid_str.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("응시 답안 형식", str(response.data))

    def test_get_submission_detail_with_list_answers_format(self) -> None:
        """
        answers가 리스트인 경우 400 확인
        """
        submission_invalid_list = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=30),
            created_at=timezone.now(),
            answers=["answer1", "answer2"],  # type: ignore
            score=0,
            correct_answer_count=0,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission_invalid_list.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("응시 답안 형식", str(response.data))

    def test_get_submission_detail_with_none_answers(self) -> None:
        """
        answers가 None인 경우 정상 처리(빈 dict로 변환)되는지 확인
        """
        submission_none = ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=timezone.now() - timedelta(minutes=30),
            created_at=timezone.now(),
            answers={},
            score=0,
            correct_answer_count=0,
            cheating_count=0,
        )

        self.client.force_authenticate(user=self.admin_user)
        url = self._get_detail_url(submission_none.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 문제가 미제출로 처리되는지 확인
        questions = response.data["questions"]
        for question in questions:
            self.assertIsNone(question["submitted_answer"])
            self.assertFalse(question["is_correct"])
