from rest_framework import serializers

from apps.courses.models import Cohort, Course, Subject


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
        fields = ["id", "course_id", "number", "start_date", "end_date", "status"]


class SubjectSerializer(serializers.ModelSerializer[Subject]):
    class Meta:
        model = Subject
        fields = [
            "id",
            "course_id",
            "title",
            "number_of_days",
            "number_of_hours",
            "thumbnail_img_url",
            "status",
            "created_at",
            "updated_at",
            "updated_at",
        ]
