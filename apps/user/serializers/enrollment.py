from typing import Any, cast

from django.utils import timezone
from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort, CohortStatusChoices
from apps.courses.models.courses_models import Course


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "number", "start_date", "end_date", "status")


class CourseAvailableSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name")


class CourseEnrolledSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name", "tag", "thumbnail_img_url")


class AvailableCourseSerializer(serializers.Serializer[Any]):
    cohort = CohortSerializer(source="*", read_only=True)
    course = CourseAvailableSerializer(read_only=True)


class EnrolledCourseItemSerializer(serializers.Serializer[Any]):
    cohort = CohortSerializer(read_only=True)
    course = CourseEnrolledSerializer(source="cohort.course", read_only=True)


class EnrollStudentSerializer(serializers.Serializer[Any]):
    cohort_id: serializers.PrimaryKeyRelatedField[Cohort] = serializers.PrimaryKeyRelatedField(
        source="cohort",
        queryset=Cohort.objects.none(),
        write_only=True,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cohort_field = cast(serializers.PrimaryKeyRelatedField[Cohort], self.fields["cohort_id"])
        cohort_field.queryset = Cohort.objects.filter(
            status=CohortStatusChoices.PENDING,
            start_date__gte=timezone.localdate(),
        ).select_related("course")
