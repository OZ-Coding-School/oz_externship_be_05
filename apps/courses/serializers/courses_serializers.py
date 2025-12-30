from rest_framework import serializers

from apps.courses.models import Cohort, Course


class CourseSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "tag",
            "description",
            "thumbnail_img_url",
            "created_at",
            "updated_at",
        ]


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "course_id", "number", "start_date", "end_date", "status")
