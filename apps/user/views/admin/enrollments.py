from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import (
    CohortStudent,
    EnrollmentStatus,
    StudentEnrollmentRequest,
    User,
)
from apps.user.models.user import RoleChoices
from apps.user.models.withdraw import Withdrawal
from apps.user.pagination import AdminAccountPagination
from apps.user.serializers.admin.enrollments import (
    AdminStudentEnrollAcceptSerializer,
    AdminStudentEnrollRejectSerializer,
    AdminStudentEnrollRequestSerializer,
    AdminStudentEnrollSerializer,
    AdminStudentSerializer,
)

ORDERING_MAP = {"id": "id", "latest": "-created_at", "oldest": "created_at"}

USER_STATUS_FILTERS = {
    "withdrew": Q(is_withdrawing=True),
    "activated": Q(is_withdrawing=False, is_active=True),
    "deactivated": Q(is_withdrawing=False, is_active=False),
}


ENROLLMENT_STATUS_FILTERS = {
    "pending": Q(status=EnrollmentStatus.PENDING),
    "accepted": Q(status=EnrollmentStatus.ACCEPTED),
    "rejected": Q(status=EnrollmentStatus.REJECTED),
    "canceled": Q(status=EnrollmentStatus.CANCELED),
}


class AdminStudentView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["회원관리"],
        summary="수강생 목록 조회 API",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["activated", "deactivated", "withdrew"],
            ),
            OpenApiParameter("course_id", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("cohort_number", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
        ],
    )
    def get(self, request: Request) -> Response:
        students = User.objects.filter(role=RoleChoices.ST).order_by("id")
        students = students.annotate(is_withdrawing=Exists(Withdrawal.objects.filter(user_id=OuterRef("pk"))))

        course_id = request.query_params.get("course_id")
        cohort_number = request.query_params.get("cohort_number")

        if course_id and str(course_id).isdigit():
            students = students.filter(cohortstudent__cohort__course_id=int(course_id))

            if cohort_number and str(cohort_number).isdigit():
                students = students.filter(cohortstudent__cohort__number=int(cohort_number))

        students = students.distinct()

        students = students.prefetch_related(
            Prefetch("cohortstudent_set", queryset=CohortStudent.objects.select_related("cohort__course"))
        )

        search = request.query_params.get("search")
        if search:
            cond = Q(email__icontains=search) | Q(nickname__icontains=search) | Q(name__icontains=search)
            if search.isdigit():
                cond |= Q(id=int(search))
            students = students.filter(cond)

        status = request.query_params.get("status")
        status_query = USER_STATUS_FILTERS.get((status or "").strip())
        if status_query:
            students = students.filter(status_query)

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(students, request, view=self)

        serializer = AdminStudentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminStudentsEnrollViews(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["회원관리"],
        summary="수강생 등록 요청 목록 조회 API",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["pending", "accepted", "rejected", "canceled"],
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["id", "latest", "oldest"],
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        enrollments = (
            StudentEnrollmentRequest.objects.all().select_related("user", "cohort", "cohort__course").order_by("id")
        )

        search = request.query_params.get("search")
        if search:
            cond = Q(user__email__icontains=search) | Q(user__name__icontains=search)
            if search.isdigit():
                cond |= Q(id=int(search))
            enrollments = enrollments.filter(cond)

        status = request.query_params.get("status")
        status_query = ENROLLMENT_STATUS_FILTERS.get((status or "").strip())
        if status_query:
            enrollments = enrollments.filter(status_query)

        ordering = (request.query_params.get("ordering") or "id").strip()

        enrollments = enrollments.order_by(ORDERING_MAP.get(ordering, "id"))

        paginator = AdminAccountPagination()
        page = paginator.paginate_queryset(enrollments, request, view=self)

        serializer = AdminStudentEnrollSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminStudentEnrollAcceptView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["회원관리"],
        summary="수강생 등록 요청 승인 API",
        request=AdminStudentEnrollRequestSerializer,
        responses={200: AdminStudentEnrollAcceptSerializer},
    )
    def post(self, request: Request) -> Response:
        req = AdminStudentEnrollRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        ids: list[int] = req.validated_data["enrollments"]

        with transaction.atomic():
            enrollments = StudentEnrollmentRequest.objects.select_for_update().filter(
                id__in=ids, status=EnrollmentStatus.PENDING
            )
            success = enrollments.update(status=EnrollmentStatus.ACCEPTED)
            failed = len(ids) - success

        data = {"detail": "수강생 등록 신청들에 대한 승인 요청이 처리되었습니다.", "success": success, "failed": failed}

        res = AdminStudentEnrollAcceptSerializer(data=data)
        res.is_valid(raise_exception=True)

        return Response(res.data, status=status.HTTP_200_OK)


class AdminStudentEnrollRejectView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["회원관리"],
        summary="수강생 등록 요청 거절 API",
        request=AdminStudentEnrollRequestSerializer,
        responses={200: AdminStudentEnrollRejectSerializer},
    )
    def post(self, request: Request) -> Response:
        req = AdminStudentEnrollRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        ids: list[int] = req.validated_data["enrollments"]

        with transaction.atomic():
            enrollments = StudentEnrollmentRequest.objects.select_for_update().filter(
                id__in=ids, status=EnrollmentStatus.PENDING
            )
            success = enrollments.update(status=EnrollmentStatus.REJECTED)
            failed = len(ids) - success

        data = {
            "detail": "수강생 등록 신청들에 대한 거절 요청이 처리되었습니다.",
            "success": success,
            "failed": failed,
        }

        res = AdminStudentEnrollRejectSerializer(data=data)
        res.is_valid(raise_exception=True)

        return Response(res.data, status=status.HTTP_200_OK)
