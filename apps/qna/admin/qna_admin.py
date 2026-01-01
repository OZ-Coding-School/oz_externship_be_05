from django.template.defaultfilters import truncatechars
from django.db.models import Count
from typing import TYPE_CHECKING
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from apps.qna.models import Question


# 런타임 에러 방지를 위한 처리
if TYPE_CHECKING:
    _QuestionBaseAdmin = admin.ModelAdmin[Question]
else:
    _QuestionBaseAdmin = admin.ModelAdmin


@admin.register(Question)
class QuestionAdmin(_QuestionBaseAdmin):
    """ 어드민 질의응답 관리"""
    # 1. [목록 조회 항목]
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

    # 2. [클릭 시 상세 페이지로 이동할 링크 설정]
    list_display_links = ("id", "title")

    # 3. [검색 설정]
    # 작성자 닉네임, 이메일, 제목, 내용으로 검색 가능
    search_fields = (
        "title",
        "content",
        "author__nickname",
        "author__email",
    )

    # 4. [필터 설정]
    list_filter = (
        "created_at",
        "category__type",  # 카테고리 타입별 필터
    )

    # 5. [기본 정렬]
    ordering = ("-created_at",)

    # 6. [성능 최적화 및 Annotation]
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