from datetime import date, timedelta
from typing import Any, Dict

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment, ExamQuestion, ExamSubmission
from apps.exams.models.exam_question import QuestionType
from apps.user.models.user import RoleChoices, User


class ExamQuestionViewTestCase(APITestCase):
    """쪽지시험 응시 문제풀이 API 테스트"""

    student_user: User
    normal_user: User
    course: Course
    cohort: Cohort
    subject: Subject
    exam: Exam
    question1: ExamQuestion
    question2: ExamQuestion
    deployment: ExamDeployment

    @classmethod
    def setUpTestData(cls) -> None:
        """
        테스트 데이터 생성
        """
        # 학생
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            name="수강생",
            password="password123",
            role=RoleChoices.ST,
            birthday=timezone.now(),
        )

        # 학생 아님
        cls.normal_user = User.objects.create_user(
            email="user@test.com",
            name="일반인",
            password="password123",
            role=RoleChoices.USER,
            birthday=timezone.now(),
        )

        # Course/Subject/Exam
        cls.course = Course.objects.create(name="야너두, 공주 할 수 있어", tag="GJ")
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        cls.subject = Subject.objects.create(
            course=cls.course,
            title="공주의 규칙",
            number_of_days=10,
            number_of_hours=20,
        )
        cls.exam = Exam.objects.create(
            title="공주 기본 화법 테스트",
            subject=cls.subject,
        )

        # 문항 생성
        cls.question1 = ExamQuestion.objects.create(
            exam=cls.exam,
            type=QuestionType.SINGLE_CHOICE,
            question="단일 선택 문제",
            point=10,
            answer="3",
            explanation="숫자 3이 좋더라",
        )
        cls.question2 = ExamQuestion.objects.create(
            exam=cls.exam,
            type=QuestionType.FILL_BLANK,
            question="빈칸 채우기",
            point=10,
            blank_count=2,
            answer=["빈", "칸"],
            explanation="설명설명",
        )

        # 배포 정보 (스냅샷 포함)
        now = timezone.now()
        cls.deployment = ExamDeployment.objects.create(
            exam=cls.exam,
            cohort=cls.cohort,
            duration_time=30,
            access_code="TEST12",
            open_at=now - timedelta(hours=1),
            close_at=now + timedelta(hours=2),
            questions_snapshot=[
                {
                    "question_id": cls.question1.id,
                    "type": "single_choice",
                    "question": "단일 선택 문제",
                    "point": 10,
                    "prompt": None,
                    "blank_count": None,
                    "options": None,
                },
                {
                    "question_id": cls.question2.id,
                    "type": "fill_blank",
                    "question": "빈칸 채우기",
                    "point": 10,
                    "prompt": None,
                    "blank_count": 2,
                    "options": None,
                },
            ],
        )

    def test_get_exam_questions_success(self) -> None:
        """
        정상 시험 문제 조회 200
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)
        data: Dict[str, Any] = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["exam_id"], self.exam.id)
        self.assertEqual(data["exam_name"], self.exam.title)
        self.assertEqual(data["duration_time"], 30)
        self.assertEqual(data["elapsed_time"], 0)
        self.assertEqual(data["cheating_count"], 0)
        self.assertEqual(len(data["questions"]), 2)

        # 첫 번째 문제 (SINGLE_CHOICE)
        q1 = data["questions"][0]
        self.assertEqual(q1["question_id"], self.question1.id)
        self.assertEqual(q1["number"], 1)
        self.assertEqual(q1["type"], "single_choice")
        self.assertIsNone(q1["answer_input"])

        # 두 번째 문제 (FILL_BLANK)
        q2 = data["questions"][1]
        self.assertEqual(q2["question_id"], self.question2.id)
        self.assertEqual(q2["number"], 2)
        self.assertEqual(q2["type"], "fill_blank")
        self.assertEqual(q2["blank_count"], 2)
        self.assertEqual(q2["answer_input"], ["", ""])

    def test_get_exam_questions_with_submission(self) -> None:
        """
        제출 내역 있으면 경과 시간, 부정행위 횟수 조회
        """
        started_at = timezone.now() - timedelta(minutes=5)
        ExamSubmission.objects.create(
            deployment=self.deployment,
            submitter=self.student_user,
            started_at=started_at,
            cheating_count=2,
            answers={},
            score=0,
            correct_answer_count=0,
        )

        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["elapsed_time"], 300)  # 5분 = 300초
        self.assertEqual(response.data["cheating_count"], 2)

    def test_get_exam_questions_forbidden_not_student(self) -> None:
        """
        일반 유저 접근 차단 테스트
        """
        self.client.force_authenticate(user=self.normal_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_exam_questions_already_ended(self) -> None:
        """
        종료된 시험 접근 시 410 Gone 테스트
        """
        self.deployment.close_at = timezone.now() - timedelta(seconds=1)
        self.deployment.save()

        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_410_GONE)

    def test_get_exam_questions_not_found(self) -> None:
        """
        존재하지 않는 배포 ID 요청 시 404 반환
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_exam_questions_not_started_yet(self) -> None:
        """
        아직 시작 전인 시험은 접근할 수 없음
        """
        now = timezone.now()
        future_deployment = ExamDeployment.objects.create(
            exam=self.exam,
            cohort=self.cohort,
            duration_time=30,
            access_code="FUTURE",
            open_at=now + timedelta(hours=1),
            close_at=now + timedelta(hours=3),
            questions_snapshot=[],  # 빈 스냅샷
        )

        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": future_deployment.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)

    def test_questions_ordered_by_number(self) -> None:
        """
        문제는 번호 순서대로 정렬되어 반환
        """
        # 3번째 문제 추가
        question3 = ExamQuestion.objects.create(
            exam=self.exam,
            question="세 번째 문제",
            type=QuestionType.OX,
            point=5,
            answer="o",
            explanation="O가 정답",
        )

        # 스냅샷에 3번째 문제 추가
        self.deployment.questions_snapshot.append(
            {
                "question_id": question3.id,
                "type": "ox",
                "question": "세 번째 문제",
                "point": 5,
                "prompt": None,
                "blank_count": None,
                "options": None,
            }
        )
        self.deployment.save()

        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)

        questions = response.data["questions"]
        numbers = [q["number"] for q in questions]

        # 번호가 1부터 시작하고 순서대로 정렬되어 있는지 확인
        self.assertEqual(numbers, [1, 2, 3])
        self.assertEqual(numbers, sorted(numbers))

    def test_questions_snapshot_used_not_db(self) -> None:
        """
        스냅샷의 문제를 사용하며, DB 문제 변경에 영향받지 않음
        """
        # DB의 문제 내용 변경
        self.question1.question = "변경된 문제"
        self.question1.save()

        self.client.force_authenticate(user=self.student_user)
        url = reverse("exam_taking", kwargs={"deployment_id": self.deployment.id})
        response = self.client.get(url)

        questions = response.data["questions"]
        # 스냅샷의 원래 내용이 반환되어야 함
        self.assertEqual(questions[0]["question"], "단일 선택 문제")
        self.assertNotEqual(questions[0]["question"], "변경된 문제")
