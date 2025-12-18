from typing import TYPE_CHECKING, Any

from django.contrib import admin

from apps.community.admin.utils.filter import TimeOrderingFilter
from apps.courses.models import Cohort

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin as _ModelAdmin

    BaseAdmin = _ModelAdmin[Cohort]
else:
    from django.contrib.admin import ModelAdmin as BaseAdmin


@admin.register(Cohort)
class CohortAdmin(BaseAdmin):
    fields = (
        "id",
        "created_at",
        "updated_at",
        "course",
        "course_info_display",
        "number",
        "max_student",
        "status",
        "start_date",
        "end_date",
        "display_students",
    )
    list_display = (
        "id",
        "course",
        "display_number",
        "display_max_student",
        "status",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "id",
        "course",
        "status",
        "number",
        "max_student",
        "created_at",
        "updated_at",
        "course_info_display",
        "display_students",
    )
    search_fields = ("number",)
    date_hierarchy = "created_at"
    list_filter = (
        TimeOrderingFilter,
        "status",
        "course",
    )


    @admin.display(description="기수", ordering="number")
    def display_number(self, obj: Cohort) -> str:
        return f"{obj.number}기"

    @admin.display(description="최대 인원", ordering="max_student")
    def display_max_student(self, obj: Cohort) -> str:
        if obj.max_student:
            return f"{obj.max_student}명"
        return "-"

    @admin.display(description="과정 정보")
    def course_info_display(self, obj: Cohort) -> str:
        tag = obj.course.tag if obj.course.tag else "태그 없음"
        description = obj.course.description if obj.course.description else "설명 없음"

        return f"태그: {tag} \n \n 설명: {description}"

    @admin.display(description="등록 학생")
    def display_students(self, obj: Cohort) -> str:
        students_query = obj.cohortstudent.select_related("user")

        if students_query:  # .exists 존재여부 체크
            student_names = [s.user.name for s in students_query if s.user.name]
            return "\n".join(student_names) + "\n \n ( 수강생이 있을시 기수 삭제 불가. )"

        return "학생 없음"

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        if obj and obj.cohortstudent.exists():
            return False
        return super().has_delete_permission(request, obj)
