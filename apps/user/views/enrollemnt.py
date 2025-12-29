from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import User
from apps.user.serializers.enrollment import (
    AvailableCourseSerializer,
    EnrolledCourseItemSerializer,
    EnrollStudentSerializer,
)


def get_authenticated_user(request: Request) -> User:
    user = request.user
    if not isinstance(user, User):
        raise NotAuthenticated()
    return user


from apps.user.utils.enrollment import (
    get_available_cohorts_queryset,
    get_user_enrolled_cohort_students,
)


class EnrollStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="수강생 등록 신청 API",
        responses={201: None},
    )
    def post(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = EnrollStudentSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "수강생 등록 신청완료."}, status=status.HTTP_201_CREATED)


class AvailableCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="현재 가능한 수강 신청 목록 받아오기 API",
        responses={200: None},
    )
    def get(self, request: Request) -> Response:
        cohorts = get_available_cohorts_queryset().select_related("course")
        serializer = AvailableCourseSerializer(cohorts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EnrolledCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["회원관리"],
        summary="내 수강 목록 받아오기 API",
        responses={200: None},
    )
    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        enrolled = get_user_enrolled_cohort_students(user=user)
        serializer = EnrolledCourseItemSerializer(enrolled, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
