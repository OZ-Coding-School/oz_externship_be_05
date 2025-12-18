from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import CohortStudent, User
from apps.user.serializers.enrollment import EnrolledCourseSerializer, EnrollmentRequestSerializer


class EnrollStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = EnrollmentRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        return Response(
            {
                "id": enrollment.id,
                "cohort_id": enrollment.cohort_id,
                "status": enrollment.status,
                "created_at": enrollment.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


class EnrolledCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        assert isinstance(request.user, User)
        entries = (
            CohortStudent.objects.select_related("cohort__course").filter(user=request.user).order_by("-created_at")
        )
        data = [
            {
                "cohort": {
                    "id": entry.cohort.id,
                    "number": entry.cohort.number,
                    "start_date": entry.cohort.start_date,
                    "end_date": entry.cohort.end_date,
                    "status": entry.cohort.status,
                },
                "course": {
                    "id": entry.cohort.course.id,
                    "name": entry.cohort.course.name,
                    "tag": entry.cohort.course.tag,
                    "thumbnail_img_url": entry.cohort.course.thumbnail_img_url,
                },
            }
            for entry in entries
        ]
        serializer = EnrolledCourseSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
