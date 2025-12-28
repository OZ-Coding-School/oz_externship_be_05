from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q
from drf_spectacular.utils import extend_schema
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
    #! students에 왜 role이 쿼리파라메터에 있는지 물어보고 불필요 하니깐 삭제 요청.
    #! 과정별 기수별 필터링을 추가해야함.
    """
    과정별, 기수별 필터링이 있는데 쿼리 파라메터에는 없음. 그러면 추가해야하나?
    그냥 검색 가능하도록 하는건지 아니면...
    """

    # ? 과정별 필터링 + 기수별 필터링 기능 추가.
    @extend_schema(tags=["회원관리"], summary="수강생 목록 조회 API")
    def get(self, request: Request) -> Response:
        students = User.objects.filter(role=RoleChoices.ST).order_by("id")
        students = students.annotate(is_withdrawing=Exists(Withdrawal.objects.filter(user_id=OuterRef("pk"))))

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
    #! API 명세서랑 status_choices값이 다름.
    #! 정렬 방식 API명세서 쿼리 파라메터에 수정해야함.
    """
    AdminStudentsEnrollViews의 Docstring
    필터링 조건 : 상태별 필터링
    정렬 기준 : ID, 최신순, 오래된 순
    """
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["회원관리"], summary="수강생 등록 요청 목록 조회 API")
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
