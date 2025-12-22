from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.courses.models import Cohort, Course, Subject
from apps.courses.models.cohorts_models import CohortStatusChoices

User = get_user_model()


class BaseCourseTestCase(APITestCase):
    """
    관리자 만들기 귀찮아서 만들엇습니다 상속받아서 쓰세요!
    """

    def setUp(self) -> None:
        # 1. 관리자 생성 및 강제 인증
        self.admin_user = get_user_model().objects.create_superuser(
            name="testuser",
            email="test@test.com",
            password="qwer1234!",
            birthday=date(2007, 8, 31),
        )
        self.client.force_authenticate(user=self.admin_user)

        # 2. 과정 생성
        self.course = Course.objects.create(
            name="테스트 과정",
            tag=1,
            description="테스트 과정",
            thumbnail_img_url="https://example.com/test.jpg",
        )
        # 3. 수강중 기수 생성
        self.active_cohort = Cohort.objects.create(
            course=self.course,
            number=1,
            max_student=10,
            start_date="2025-01-01",
            end_date="2025-12-31",
            status=CohortStatusChoices.IN_PROGRESS,
        )
        # 4. 대기중 기수 생성
        self.pending_cohort = Cohort.objects.create(
            course=self.course,
            number=3,
            max_student=10,
            start_date="2025-01-01",
            end_date="2025-12-31",
            status=CohortStatusChoices.PENDING,
        )

        # 5. 수료 기수 생성
        self.completed_cohort = Cohort.objects.create(
            course=self.course,
            number=2,
            max_student=10,
            start_date="2024-01-01",
            end_date="2024-12-31",
            status=CohortStatusChoices.COMPLETED,
        )

        # 6. 과목 생성
        self.subject = Subject.objects.create(
            title="테스트 과목",
            course=self.course,
            number_of_days=5,
            number_of_hours=40,
            status=True,
            thumbnail_img_url="https://example.com/test.jpg",
        )
