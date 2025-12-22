from django.db.models import Prefetch, Q
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.courses.models import Course
from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.serializers.courses_serializers import CourseCohortsSerializer


class CourseCohortsView(APIView):
    # permission_classes = [IsAdminUser]

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
