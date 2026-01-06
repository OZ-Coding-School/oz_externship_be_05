from typing import TYPE_CHECKING, Any, Optional

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils.html import format_html

from apps.qna.models.question.question_category import QuestionCategory

# 런타임 에러 방지를 위한 처리
if TYPE_CHECKING:
    _BaseAdmin = admin.ModelAdmin[QuestionCategory]
else:
    _BaseAdmin = admin.ModelAdmin


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(_BaseAdmin):
    """어드민 카테고리 관리"""

    # 1. [목록 조회 시 보여줄 항목]
    list_display = (
        "id",
        "name",
        "get_type_display_custom",
        "get_children_names",
        "get_parent_name",
        "created_at",
        "updated_at",
    )

    # 2. [검색 및 필터 설정]
    list_filter = ("type", "created_at")
    search_fields = ("name", "parent__name")
    ordering = ("type", "parent", "id")

    # 3. [성능 최적화]
    def get_queryset(self, request: HttpRequest) -> QuerySet[QuestionCategory]:
        queryset = super().get_queryset(request)
        return queryset.select_related("parent").prefetch_related("children")

    # --- [삭제 시 경고 메시지 출력] ---
    def delete_view(
        self, request: HttpRequest, object_id: str, extra_context: Optional[dict[str, Any]] = None
    ) -> HttpResponse:
        obj = self.get_object(request, object_id)
        extra_context = extra_context or {}

        if obj:
            warning_msg = ""
            base_msg = " 해당 카테고리의 질의응답은 '일반질문'으로 자동 전환되며, 삭제된 카테고리는 복구할 수 없습니다."

            if obj.type == "large":
                warning_msg = f"⚠️ [대분류 삭제 경고] 하위 '중분류' 및 '소분류'가 모두 함께 삭제됩니다!{base_msg}"
            elif obj.type == "medium":
                warning_msg = f"⚠️ [중분류 삭제 경고] 하위 '소분류'가 모두 함께 삭제됩니다!{base_msg}"
            else:  # small
                warning_msg = f"⚠️ [소분류 삭제 경고]{base_msg}"

            extra_context["title"] = warning_msg

        return super().delete_view(request, object_id, extra_context=extra_context)

    # --- [커스텀 컬럼 메서드: 색상 적용 ] ---
    @admin.display(description="분류 타입")
    def get_type_display_custom(self, obj: QuestionCategory) -> str:
        # 1. 타입별 색상 매핑 (Bootstrap 색상 참고)
        color_map = {
            "large": "28a745",  # Green (대분류)
            "medium": "17a2b8",  # Cyan (중분류)
            "small": "6c757d",  # Grey (소분류)
        }
        color = color_map.get(obj.type, "333")  # 기본값: 검정

        # 2. format_html로 안전하게 뱃지 생성
        return format_html(
            '<span style="color: white; background-color: #{}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display(),
        )

    @admin.display(description="자식 카테고리")
    def get_children_names(self, obj: QuestionCategory) -> str:
        if obj.type == "small":
            return "-"
        children = obj.children.all()
        return ", ".join([child.name for child in children]) if children else "-"

    @admin.display(description="부모 카테고리")
    def get_parent_name(self, obj: QuestionCategory) -> str:
        if obj.type == "large":
            return "-"
        return f"{obj.parent.name} ({obj.parent.get_type_display()})" if obj.parent else "-"
