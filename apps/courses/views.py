from django.shortcuts import render
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from apps.courses.models import Course
from apps.courses.models.cohorts_models import CohortStatusChoices
from apps.courses.serializers.courses_serializers import CourseCohortSerializer


class CohortsListView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = CourseCohortSerializer

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')

        return Course.objects.filter(
            course_id=course_id,
            status=CohortStatusChoices.IN_PROGRESS,
        ).order_by('number')