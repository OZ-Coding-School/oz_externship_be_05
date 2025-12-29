from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.courses.models import Course
from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.serializers.courses_serializers import CourseCohortsSerializer
from apps.courses.serializers.enrollment import AvailableCourseSerializer


@extend_schema(
    summary="해당 과정 진행중인 기수 조회 API",
    tags=["과정-기수 관리"],
)
class CourseCohortsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        try:
            courses = Course.objects.prefetch_related(
                Prefetch(
                    "cohorts",
                    queryset=Cohort.objects.filter(
                        Q(status=CohortStatusChoices.IN_PROGRESS) | Q(status=CohortStatusChoices.PENDING)
                    ),
                    to_attr="select_enable_cohorts",
                )
            ).all()
        except Course.DoesNotExist:
            return Response(EMS.E404_NOT_FOUND("과정 정보"), status=status.HTTP_404_NOT_FOUND)

        return Response(CourseCohortsSerializer(courses, many=True).data)


class AvailableCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="현재 가능한 수강 신청 목록 받아오기 API",
        responses={200: None},
    )
    def get(self, request: Request) -> Response:
        cohorts = Cohort.objects.filter(
            status=CohortStatusChoices.PENDING, start_date__gte=timezone.localdate()
        ).select_related("course")
        serializer = AvailableCourseSerializer(cohorts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
