from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import CohortStudent, User
from apps.user.serializers.enrollment import (
    EnrolledCourseItemSerializer,
    EnrollStudentSerializer,
)
from apps.user.services.enrollment_service import enroll_student


class EnrollStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        summary="Enroll student request",
        request=EnrollStudentSerializer,
        responses={201: None},
    )
    def post(self, request: Request) -> Response:
        serializer = EnrollStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enroll_student(user=cast(User, request.user), cohort=serializer.validated_data["cohort"])
        return Response({"detail": "수강생 등록 신청완료."}, status=status.HTTP_201_CREATED)


class EnrolledCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        summary="Get enrolled courses",
        responses=EnrolledCourseItemSerializer,
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        enrolled = CohortStudent.objects.filter(user=user).select_related("cohort", "cohort__course")
        serializer = EnrolledCourseItemSerializer(enrolled, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
