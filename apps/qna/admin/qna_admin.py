from django.template.defaultfilters import truncatechars
from django.db.models import Count, QuerySet
from typing import TYPE_CHECKING
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from apps.qna.admin.utils.user_info import get_user_display_info
from apps.qna.models import Question, Answer


# 런타임 에러 방지를 위한 처리
if TYPE_CHECKING:
    _QuestionBaseAdmin = admin.ModelAdmin[Question]
    _AnswerInlineBase = admin.StackedInline
else:
    _QuestionBaseAdmin = admin.ModelAdmin
    _AnswerInlineBase = admin.StackedInline

# 답변 처리
class AnswerInline(_AnswerInlineBase):
    model = Answer
    extra = 0
    verbose_name = "등록된 답변"
    verbose_name_plural = "답변 목록"

    readonly_fields = (
        "get_answerer_info",
        "created_at",
        "updated_at"
    )

    fieldsets = (
        (None, {
            "fields": ("get_answerer_info", "content", "is_adopted", "created_at")
        }),
    )

    @admin.display(description="답변 작성자")
    def get_answerer_info(self, obj):
        return get_user_display_info(obj.author)


@admin.register(Question)
class QuestionAdmin(_QuestionBaseAdmin):
    # [목록 조회 항목]
    list_display = (
        "id",
        "title",
        "get_category_hierarchy",  # 카테고리 경로
        "get_content_preview",  # 내용 미리보기
        "get_author_nickname",  # 작성자 닉네임
        "view_count",
        "get_is_answered",  # 답변 여부 (Y/N)
        "created_at",
        "updated_at",
    )

    # [(목록 조회) 클릭 시 상세 페이지로 이동할 링크 설정]
    list_display_links = ("id", "title")

    # [(목록 조회) 검색 설정]
    # 작성자 닉네임, 이메일, 제목, 내용으로 검색 가능
    search_fields = (
        "title",
        "content",
        "author__nickname",
        "author__email",
    )

    # [(목록 조회) 필터 설정]
    list_filter = (
        "created_at",
        "category__type",  # 카테고리 타입별 필터
    )

    # [(목록 조회) 기본 정렬]
    ordering = ("-created_at",)

    # [상세 조회 설정]
    inlines = [AnswerInline]

    fieldsets = (
        ("질문 상세 정보", {
            "fields": ("get_questioner_details",
                       "title",
                       "get_category_hierarchy",
                       "content",
                       "view_count",
                       "get_is_answered_text",
                       "created_at",
                       "updated_at"
                       )
        }),
    )

    readonly_fields = (
        "get_category_hierarchy", "get_questioner_details",
        "get_is_answered_text", "created_at", "updated_at", "view_count"
    )

    # [성능 최적화 및 Annotation]
    def get_queryset(self, request: HttpRequest) -> QuerySet[Question]:
        """
        답변 개수를 미리 계산(annotate)
        """
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "author",
            "category",
            "category__parent",
            "category__parent__parent"
        ).annotate(
            answers_count=Count("answers")
        )

    # --- [커스텀 메서드 정의] ---

    @admin.display(description="카테고리 경로")
    def get_category_hierarchy(self, obj: Question) -> str:
        """대분류 > 중분류 > 소분류 형태로 표시"""
        category = obj.category
        path = []

        # 현재 카테고리부터 부모를 타고 올라가며 경로 수집
        current = category
        while current:
            path.append(current.name)
            current = current.parent

        # [소, 중, 대] -> [대, 중, 소] 순서로 뒤집고 화살표로 연결
        full_path = " > ".join(reversed(path))
        return full_path

    # --- [ 질문 조회 메서드 ] ---
    @admin.display(description="내용")
    def get_content_preview(self, obj: Question) -> str:
        """내용이 길 경우 30자로 자름"""
        return truncatechars(obj.content, 30)

    @admin.display(description="작성자", ordering="author__nickname")
    def get_author_nickname(self, obj: Question) -> str:
        """작성자 닉네임 표시(없을 경우 작성자의 이름)"""
        return getattr(obj.author, "nickname", obj.author.name)

    @admin.display(description="답변 여부", ordering="answers_count")
    def get_is_answered(self, obj: Question) -> str:
        """
        답변 개수(answers_count)를 기반으로 Y/N 표시
        """
        has_answer = getattr(obj, "answers_count", 0) > 0

        if has_answer:
            # 초록색 Y 뱃지
            return format_html(
                '<span style="color: white; background-color: #28a745; padding: 4px 8px; border-radius: 50%;">Y</span>'
            )
        else:
            # 회색 N 뱃지
            return format_html(
                '<span style="color: white; background-color: #dc3545; padding: 4px 8px; border-radius: 50%;">N</span>'
            )

    # --- [ 질문 상세 조회 메서드 ] ---
    @admin.display(description="질문 작성자 정보")
    def get_questioner_details(self, obj: Question) -> str:
        return get_user_display_info(obj.author)

    @admin.display(description="답변 여부")
    def get_is_answered_text(self, obj: Question) -> str:
        cnt = getattr(obj, "answers_count", obj.answers.count())
        return f"Y (총 {cnt}건)" if cnt > 0 else "N"






