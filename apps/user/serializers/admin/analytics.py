from typing import Any

from rest_framework import serializers


class PeriodCountItemSerializer(serializers.Serializer[dict[str, Any]]):
    period = serializers.CharField()
    count = serializers.IntegerField(min_value=0)


class AdminAnalyticsSignupWithdrawalTrendSerializer(serializers.Serializer[dict[str, Any]]):
    interval = serializers.ChoiceField(choices=("monthly", "yearly"))
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField(min_value=0)
    items = PeriodCountItemSerializer(many=True)


class AdminWithdrawalTrendQuerySerializer(serializers.Serializer[dict[str, Any]]):
    interval = serializers.ChoiceField(choices=("monthly", "yearly"), required=False, default="monthly")
    years = serializers.IntegerField(required=False, min_value=1, max_value=50, default=5)
