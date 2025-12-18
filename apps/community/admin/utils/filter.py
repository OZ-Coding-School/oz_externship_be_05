from typing import Any

from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.db.models import Count, F, Q, QuerySet, Sum
from django.http import HttpRequest

from apps.courses.models.cohorts_models import CohortStatusChoices

# 정렬


class TimeOrderingFilter(SimpleListFilter):
    title = "시간 정렬"
    parameter_name = "order_by_time"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("latest", "최신순"),
            ("oldest", "오래된 순"),
        ]

    def queryset(self, request: Any, queryset: Any) -> Any:

        if self.value() == "latest":
            return queryset.order_by("-created_at")

        if self.value() == "oldest":
            return queryset.order_by("created_at")

        return queryset  # ordering 작동


class PostOrderingFilter(TimeOrderingFilter):
    title = "정렬 기준"
    parameter_name = "post_order_by"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[str, str]]:
        time_options = super().lookups(request, model_admin)

        post_options = [
            ("most_views", "조회수 많은 순"),
            ("most_likes", "좋아요 많은 순"),
        ]

        return time_options + post_options

    def queryset(self, request: Any, queryset: QuerySet[Any]) -> Any:

        if self.value() == "most_views":
            return queryset.order_by("-view_count")

        if self.value() == "most_likes":
            return queryset.order_by("-_likes_count")

        return super().queryset(request, queryset)  # ordering 작동


# 검색 필터
class CustomSearchFilter(SimpleListFilter):
    title = "검색 대상"
    parameter_name = "search_target"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("author", "사용자"),
            ("title", "제목"),
            ("content", "내용"),
            ("title_content", "제목 + 내용"),
        ]

    def queryset(self, request: Any, queryset: Any) -> Any:
        target = self.value()
        query = request.GET.get("q")

        if not query:
            return queryset

        if target == "author":
            return queryset.filter(author__nickname__icontains=query)

        if target == "title":
            return queryset.filter(title__icontains=query)

            # '내용만 검색'을 선택했을 때
        if target == "content":
            return queryset.filter(content__icontains=query)

        if target == "title_content" or target is None:
            return queryset.filter(Q(title__icontains=query) | Q(content__icontains=query))

        return queryset
