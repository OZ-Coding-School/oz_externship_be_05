from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception_messages import EMS
from apps.courses.models import Course
from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.serializers.courses_serializers import CourseCohortSerializer


class CohortsListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, course_id: int) -> Response:

        if not Course.objects.filter(id=course_id).exists():
            return Response(EMS.E404_NOT_FOUND("과정 정보"), status=status.HTTP_404_NOT_FOUND)

        cohorts = Cohort.objects.filter(
            course_id=course_id,
            status=CohortStatusChoices.IN_PROGRESS,
        ).order_by("number")

        serializer = CourseCohortSerializer(cohorts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
