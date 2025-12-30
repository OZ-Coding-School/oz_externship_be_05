from typing import Any

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, Subject
from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.serializers.courses_serializers import (
    CohortSerializer,
    CourseSerializer,
    SubjectSerializer,
)
from apps.courses.serializers.enrollment import AvailableCourseSerializer


@extend_schema(
    summary="기수 리스트 조회 API",
    tags=["과정-기수 관리"],
)
class CohortListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        course_id = kwargs.get("course_id")
        cohort = Cohort.objects.filter(course=course_id)
        return Response(CohortSerializer(cohort, many=True).data)


@extend_schema(
    summary="과목 리스트 조회 API",
    tags=["수강 과목 관리"],
)
class SubjectListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        course_id = kwargs.get("course_id")
        subject = Subject.objects.filter(course=course_id)
        return Response(SubjectSerializer(subject, many=True).data)


@extend_schema(
    summary="과정 리스트 조회 API",
    tags=["과정-기수 관리"],
)
class CourseListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request: Request) -> Response:
        course = Course.objects.all()
        return Response(CourseSerializer(course, many=True).data)


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
