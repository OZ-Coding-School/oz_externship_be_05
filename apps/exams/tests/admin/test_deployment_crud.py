import uuid
from datetime import date, timedelta
from typing import Any, List

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.utils.base62 import Base62
from apps.courses.models import Cohort, Course, Subject
from apps.exams.models import Exam, ExamDeployment
from apps.exams.models.exam_deployment import DeploymentStatus
from apps.exams.services.admin.admin_deployment_service import (
    create_deployment,
)
from apps.user.models.user import GenderChoices, RoleChoices, User

DEFAULT_DURATION_TIME = 60
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DeploymentListCreateAPIViewTestCase(APITestCase):
    course: Course
    subject: Subject
    cohort: Cohort
    exam: Exam
    admin_user: User
    normal_user: User
    deployments: List[ExamDeployment]
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        # Course / Subject / Exam / Cohort
        cls.course = Course.objects.create(name="테스트 과정")
        cls.subject = Subject.objects.create(
            title="테스트 과목",
            course=cls.course,
            number_of_days=10,
            number_of_hours=20,
        )
        cls.cohort = Cohort.objects.create(
            number=1,
            course=cls.course,
            max_student=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        cls.exam = Exam.objects.create(title="테스트 시험", subject=cls.subject)

        # Users
        cls.admin_user = User.objects.create_superuser(
            name="admin",
            password="password123",
            email="admin@test.com",
            phone_number="010-1234-1234",
            gender=GenderChoices.MALE,
            birthday=date.today() + timedelta(days=30),
        )
        cls.normal_user = User.objects.create_user(
            password="password123",
            email="user@test.com",
            name="user",
            phone_number="010-1234-5678",
            gender=GenderChoices.FEMALE,
            birthday=date.today() - timedelta(days=30),
        )

        # ExamDeployments (15개)
        cls.deployments = [
            ExamDeployment.objects.create(
                exam=cls.exam,
                cohort=cls.cohort,
                duration_time=DEFAULT_DURATION_TIME,
                access_code=Base62.uuid_encode(uuid.uuid4(), length=6),
                open_at=timezone.now() + timedelta(hours=1),
                close_at=timezone.now() + timedelta(hours=5),
                questions_snapshot=[],
            )
            for _ in range(15)
        ]

        cls.url = reverse("exam-deployments")

    # APITestCase용 헬퍼 메서드
    def _create_default_deployment(self, **override: Any) -> ExamDeployment:
        self._deployment_counter = getattr(self, "_deployment_counter", 0) + 1
        offset = timedelta(minutes=10 * self._deployment_counter)

        pop = override.pop

        # 항상 새로운 cohort를 생성
        cohort = pop("cohort", None)
        if cohort is None:
            cohort = Cohort.objects.create(
                course=self.course,
                number=100 + self._deployment_counter,  # 중복 방지
                max_student=30,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=30),
            )

        exam = pop("exam", self.exam)
        open_at = pop("open_at", timezone.now() + offset)
        close_at = pop("close_at", open_at + timedelta(hours=1))
        duration_time = pop("duration_time", DEFAULT_DURATION_TIME)

        return create_deployment(
            cohort=cohort,
            exam=exam,
            duration_time=duration_time,
            open_at=open_at,
            close_at=close_at,
        )

    # --------------------
    # GET tests
    # --------------------

    def test_get_deployments_as_admin_success(self) -> None:
        """관리자 조회 성공 및 기본 응답 구조 확인"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_json = response.json()
        self.assertIn("count", response_json)
        self.assertIn("results", response_json)

        self.assertEqual(response_json["count"], 15)
        self.assertEqual(len(response_json["results"]), 10)

        first_deployment = response_json["results"][0]
        self.assertIn("id", first_deployment)
        self.assertIn("exam", first_deployment)
        self.assertIn("cohort", first_deployment)

    def test_get_deployments_as_normal_user_forbidden(self) -> None:
        """일반 유저(403 Forbidden)"""
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pagination_size_parameter(self) -> None:
        """size 파라미터로 페이지네이션 동작 확인"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"page": 1, "size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["size"], 5)

    def test_filter_by_cohort_id(self) -> None:
        """cohort_id 파라미터로 배포 필터링 확인"""
        self.client.force_authenticate(user=self.admin_user)

        other_cohort = Cohort.objects.create(
            number=2,
            course=self.course,
            max_student=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        create_deployment(
            cohort=other_cohort,
            exam=self.exam,
            duration_time=DEFAULT_DURATION_TIME,
            open_at=timezone.now() + timedelta(hours=1),
            close_at=timezone.now() + timedelta(hours=5),
        )

        response = self.client.get(self.url, {"cohort_id": other_cohort.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["cohort"]["number"],
            other_cohort.number,
        )

    def test_filter_by_subject_id(self) -> None:
        """subject_id 파라미터로 배포 필터링 확인"""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"subject_id": self.subject.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)

    def test_sorting_by_created_at_desc(self) -> None:
        """created_at desc 정렬 확인"""
        self.admin_user.role = RoleChoices.AD
        self.admin_user.save()
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, query_params={"sort": "created_at", "order": "desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        latest_id = self.deployments[-1].id
        self.assertEqual(response.data["results"][0]["id"], latest_id)

    def test_invalid_query_params(self) -> None:
        """잘못된 query parameter(int가 아님) 입력 시 400 Bad Request 확인"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"cohort_id": "abc", "page": "xyz"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --------------------
    # POST tests
    # --------------------
    def test_create_deployment_success(self) -> None:
        """관리자가 올바른 데이터로 배포 생성 시 201 Created 확인"""
        self.client.force_authenticate(user=self.admin_user)

        # 중복을 피하기 위해 새로운 cohort 생성
        new_cohort = Cohort.objects.create(
            number=99,
            course=self.course,
            max_student=20,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        data = {
            "cohort_id": new_cohort.id,
            "exam_id": self.exam.id,
            "duration_time": DEFAULT_DURATION_TIME,
            "open_at": (timezone.now() + timedelta(minutes=1)).isoformat(),
            "close_at": (timezone.now() + timedelta(hours=2)).isoformat(),
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_json = response.json()
        self.assertIn("pk", response_json)
        self.assertIsInstance(response_json["pk"], int)

    def test_create_deployment_forbidden_for_normal_user(self) -> None:
        """일반 유저가 배포 생성 시 403 Forbidden 확인"""
        self.client.force_authenticate(user=self.normal_user)
        data = {
            "cohort_id": self.cohort.id,
            "exam_id": self.exam.id,
            "duration_time": DEFAULT_DURATION_TIME,
            "open_at": timezone.now(),
            "close_at": timezone.now() + timedelta(hours=2),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_deployment_invalid_data(self) -> None:
        """유효하지 않은 데이터 입력 시 400 Bad Request 확인"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "cohort_id": "",
            "exam_id": self.exam.id,
            "duration_time": "abc",
            "open_at": timezone.now(),
            "close_at": timezone.now() + timedelta(hours=2),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deployment_not_found(self) -> None:
        """존재하지 않는 cohort 또는 exam으로 생성 시 404 Not Found 확인"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "cohort_id": 9999,
            "exam_id": 9999,
            "duration_time": DEFAULT_DURATION_TIME,
            "open_at": timezone.now(),
            "close_at": timezone.now() + timedelta(hours=2),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_create_deployment_duplicate(self) -> None:
        """이미 존재하는 cohort+exam 배포 생성 시 409 Conflict 확인"""
        self.client.force_authenticate(user=self.admin_user)
        existing = self.deployments[0]

        # 활성화 상태 + open_at <= now로 설정
        existing.status = DeploymentStatus.ACTIVATED
        existing.open_at = timezone.now() - timedelta(minutes=1)
        existing.save(update_fields=["status", "open_at"])

        data = {
            "cohort_id": existing.cohort.id,
            "exam_id": existing.exam.id,
            "duration_time": DEFAULT_DURATION_TIME,
            "open_at": (timezone.now() + timedelta(minutes=1)).isoformat(),
            "close_at": (timezone.now() + timedelta(hours=2)).isoformat(),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn(
            f"동일한 조건의 배포가 이미 존재합니다: '{existing.exam.title}' - {existing.cohort.number}기",
            response.data["error_detail"],
        )

    # --------------------
    # GET DETAIL tests
    # --------------------

    def test_get_deployment_detail_as_admin_success(self) -> None:
        """관리자 배포 상세 조회 성공"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[0]
        url = reverse(
            "exam-deployment-detail",
            kwargs={"deployment_id": deployment.id},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("exam", response.data)
        self.assertIn("subject", response.data)
        self.assertIn("deployment", response.data)

        deployment_data = response.data["deployment"]
        self.assertEqual(deployment_data["id"], deployment.id)
        self.assertIn("exam_access_url", deployment_data)
        self.assertIn("submit_count", deployment_data)
        self.assertIn("not_submitted_count", deployment_data)
        self.assertIn("cohort", deployment_data)

    def test_get_deployment_detail_forbidden_for_normal_user(self) -> None:
        """일반 유저 배포 상세 조회 시 403"""
        self.client.force_authenticate(user=self.normal_user)

        deployment = self.deployments[0]
        url = reverse(
            "exam-deployment-detail",
            kwargs={"deployment_id": deployment.id},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --------------------
    # PATCH tests (Update Deployment)
    # --------------------

    def test_update_deployment_success(self) -> None:
        """관리자가 배포 수정 시 200 OK 및 응답값 확인"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[0]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        open_at = timezone.now() + timedelta(hours=2)
        close_at = open_at + timedelta(hours=2)

        payload = {
            "duration_time": DEFAULT_DURATION_TIME,
            "open_at": open_at.isoformat(),
            "close_at": close_at.isoformat(),
        }

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 스펙 검증
        self.assertEqual(response.data["deployment_id"], deployment.id)
        self.assertEqual(response.data["duration_time"], DEFAULT_DURATION_TIME)
        self.assertIn("open_at", response.data)
        self.assertIn("close_at", response.data)
        self.assertIn("updated_at", response.data)

        # 실제 DB 반영 여부 확인
        deployment.refresh_from_db()
        self.assertEqual(deployment.duration_time, DEFAULT_DURATION_TIME)

    def test_update_deployment_not_found(self) -> None:
        """존재하지 않는 배포 수정 시 404 Not Found"""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("exam-deployment-detail", kwargs={"deployment_id": 999999})

        response = self.client.patch(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_started_deployment_fail(self) -> None:
        """이미 시작된 시험 수정 시 400 Bad Request"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[0]
        deployment.open_at = timezone.now() - timedelta(minutes=10)
        deployment.status = DeploymentStatus.ACTIVATED
        deployment.save(update_fields=["open_at", "status"])

        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        payload = {"duration_time": DEFAULT_DURATION_TIME}

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)
        self.assertIn("open_at", response.data["errors"])

    def test_update_deployment_forbidden_for_normal_user(self) -> None:
        """일반 유저 배포 수정 시 403 Forbidden"""
        self.client.force_authenticate(user=self.normal_user)

        deployment = self.deployments[0]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        response = self.client.patch(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deployment_unauthorized(self) -> None:
        """인증 없이 배포 수정 시 401 Unauthorized"""
        self.client.force_authenticate(user=None)

        deployment = self.deployments[0]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        response = self.client.patch(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_duration_time_less_than_30(self) -> None:
        """시험 시간(duration_time) 30분 미만이면 배포 수정 실패 확인"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[0]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        payload = {"duration_time": 20}

        response = self.client.patch(url, payload, format="json")

        self.assertIn("errors", response.data)
        self.assertIn("duration_time", response.data["errors"])

    # --------------------
    # DELETE tests
    # --------------------
    def test_delete_deployment_success(self) -> None:
        """배포 삭제 시 200 OK 및 데이터 삭제 확인"""
        self.client.force_authenticate(user=self.admin_user)
        deployment = self.deployments[0]
        deployment_id = deployment.id
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment_id})

        response = self.client.delete(url)

        # 응답 상태 및 데이터 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deployment_id"], deployment_id)

        # 실제 DB에서 삭제되었는지 확인
        self.assertFalse(ExamDeployment.objects.filter(id=deployment_id).exists())

    def test_delete_deployment_not_found(self) -> None:
        """존재하지 않는 배포 삭제 시 404 확인"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": 999999})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_deployment_forbidden_for_normal_user(self) -> None:
        """일반 유저가 배포 삭제 시도 시 403 확인"""
        self.client.force_authenticate(user=self.normal_user)
        deployment = self.deployments[1]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 데이터가 삭제되지 않고 남아있는지 확인
        self.assertTrue(ExamDeployment.objects.filter(id=deployment.id).exists())

    def test_delete_deployment_unauthorized(self) -> None:
        """비인증 사용자가 배포 삭제 시도 시 401 확인"""
        self.client.force_authenticate(user=None)
        deployment = self.deployments[2]
        url = reverse("exam-deployment-detail", kwargs={"deployment_id": deployment.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --------------------
    # PATCH tests
    # --------------------

    def test_patch_deployment_status_success(self) -> None:
        """관리자 배포 상태 변경 성공 (Activated -> Deactivated)"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[0]
        deployment.close_at = timezone.now() + timedelta(days=1)
        deployment.status = DeploymentStatus.ACTIVATED
        deployment.save()

        url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})
        payload = {"status": DeploymentStatus.DEACTIVATED}

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deployment_id"], deployment.id)
        self.assertEqual(response.data["status"], DeploymentStatus.DEACTIVATED)

        # DB 반영 및 즉시 종료 로직(close_at 업데이트) 확인
        deployment.refresh_from_db()
        self.assertEqual(deployment.status, DeploymentStatus.DEACTIVATED)
        # 즉시 종료 요구사항에 의해 close_at이 과거 혹은 현재로 당겨졌는지 확인
        self.assertTrue(deployment.close_at <= timezone.now())

    def test_patch_deployment_status_invalid_data_400(self) -> None:
        """잘못된 상태 값 입력 400 확인"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[4]
        url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})
        payload = {"status": "invalid_status_string"}

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_deployment_status_unauthorized_401(self) -> None:
        """비인증 유저 접근 시 401 확인"""
        deployment = self.deployments[5]
        url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})

        response = self.client.patch(url, {"status": DeploymentStatus.ACTIVATED}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_deployment_status_forbidden_403(self) -> None:
        """일반 유저 접근 시 403 확인"""
        self.client.force_authenticate(user=self.normal_user)

        deployment = self.deployments[6]
        url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})

        response = self.client.patch(url, {"status": DeploymentStatus.ACTIVATED}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_deployment_status_not_found_404(self) -> None:
        """존재하지 않는 배포 ID로 요청 시 404 확인"""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("exam-deployment-status", kwargs={"deployment_id": 999999})

        response = self.client.patch(url, {"status": DeploymentStatus.ACTIVATED}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_deployment_status_conflict_already_set_409(self) -> None:
        """이미 동일한 상태인 경우 409 확인"""
        self.client.force_authenticate(user=self.admin_user)

        deployment = self.deployments[7]
        deployment.status = DeploymentStatus.ACTIVATED
        deployment.save()

        url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})
        payload = {"status": DeploymentStatus.ACTIVATED}  # 동일한 상태 요청

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


def test_patch_deployment_status_fail_if_already_finished(self: Any) -> None:
    """이미 종료된 시험은 상태 변경 불가 400 확인"""
    self.client.force_authenticate(user=self.admin_user)
    deployment = self.deployments[8]
    url = reverse("exam-deployment-status", kwargs={"deployment_id": deployment.id})

    # 시간이 이미 지나서 종료된 경우
    deployment.close_at = timezone.now() - timedelta(days=1)
    deployment.status = DeploymentStatus.ACTIVATED
    deployment.save()

    response_1 = self.client.patch(url, {"status": DeploymentStatus.DEACTIVATED}, format="json")
    self.assertEqual(response_1.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("이미 종료된 시험은 상태를 변경할 수 없습니다.", str(response_1.data))

    # 관리자가 비활성화하여 즉시 종료된 경우
    deployment.close_at = timezone.now() + timedelta(days=1)
    deployment.save()

    self.client.patch(url, {"status": DeploymentStatus.DEACTIVATED}, format="json")

    # 다시 활성화 시도하면 400 에러
    response_2 = self.client.patch(url, {"status": DeploymentStatus.ACTIVATED}, format="json")
    self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("이미 종료된 시험은 상태를 변경할 수 없습니다.", str(response_2.data))
