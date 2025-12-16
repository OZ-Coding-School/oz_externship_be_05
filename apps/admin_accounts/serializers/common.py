from rest_framework import serializers
from apps.user.models import User
from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course

class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "tag")

class CohortMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ("id", "number", "status", "start_date", "end_date")

class CohortSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ("id", "number")

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "birthday", "gender")

class UserWithdrawalMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "birthday")

class UserWithdrawalDetailMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "gender", "role", "status", "profile_img_url", "created_at")