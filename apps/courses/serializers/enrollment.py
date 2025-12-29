from typing import Any

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "number", "start_date", "end_date", "status")

class CourseAvailableSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name")

class AvailableCourseSerializer(serializers.Serializer[Any]):
    cohort = CohortSerializer(source="*", read_only=True)
    course = CourseAvailableSerializer(read_only=True)