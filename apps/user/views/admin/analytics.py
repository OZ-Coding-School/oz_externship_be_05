from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.user import User
from apps.user.models.withdraw import Withdrawal
from apps.user.permissions import IsAdminStaffRole
from apps.user.serializers.admin.analytics import (
    AdminAnalyticsSignupWithdrawalTrendSerializer,
    AdminWithdrawalTrendQuerySerializer,
)
from apps.user.services.admin_analytics_services import Interval, get_trend


class AdminSignupStatsAPIView(APIView):
    permission_classes = [IsAdminStaffRole]

    @extend_schema(
        tags=["회원관리"],
        summary="회원가입 내역 목록 조회 API",
        parameters=[
            OpenApiParameter(
                "interval",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["monthly", "yearly"],
            )
        ],
    )
    def get(self, request: Request) -> Response:
        q = AdminWithdrawalTrendQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)

        interval: Interval = q.validated_data["interval"]
        years: int = q.validated_data["years"]

        result = get_trend(model=User, interval=interval, years=years)

        payload = {
            "interval": result.interval,
            "from_date": result.from_date,
            "to_date": result.to_date,
            "total": result.total,
            "items": result.items,
        }

        out = AdminAnalyticsSignupWithdrawalTrendSerializer(data=payload)
        out.is_valid(raise_exception=True)
        return Response(out.data, status=status.HTTP_200_OK)


class AdminWithdrawalStatsAPIView(APIView):
    permission_classes = [IsAdminStaffRole]

    @extend_schema(
        tags=["회원관리"],
        summary="회원탈퇴 내역 목록 조회 API",
        parameters=[
            OpenApiParameter(
                "interval",
                OpenApiTypes.STR,
                required=False,
                location=OpenApiParameter.QUERY,
                enum=["monthly", "yearly"],
            )
        ],
    )
    def get(self, request: Request) -> Response:
        q = AdminWithdrawalTrendQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)

        interval: Interval = q.validated_data["interval"]
        years: int = q.validated_data["years"]

        result = get_trend(model=Withdrawal, interval=interval, years=years)

        payload = {
            "interval": result.interval,
            "from_date": result.from_date,
            "to_date": result.to_date,
            "total": result.total,
            "items": result.items,
        }

        out = AdminAnalyticsSignupWithdrawalTrendSerializer(data=payload)
        out.is_valid(raise_exception=True)
        return Response(out.data, status=status.HTTP_200_OK)
