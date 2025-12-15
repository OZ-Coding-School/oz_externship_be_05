from django.contrib.admin import SimpleListFilter
from django.db.models import Count

from django.db.models import Q


# 정렬
class PostOrderingFilter(SimpleListFilter):
    title = '정렬 기준'
    parameter_name = 'order_by'

    def lookups(self, request, model_admin) -> list:
        return [
            ('latest', '최신순'),
            ('oldest', '오래된 순'),
            ('most_views', '조회수 많은 순'),
            ('most_likes', '좋아요 많은 순'),
        ]

    def queryset(self, request, queryset):

        if self.value() == 'latest':
            return queryset.order_by('-created_at')

        if self.value() == 'oldest':
            return queryset.order_by('created_at')

        if self.value() == 'most_views':
            return queryset.order_by('-view_count')

        if self.value() == 'most_likes':
            return queryset.annotate(like_count=Count('post_likes')).order_by('-like_count')

        return None # ordering 작동


class TimeOrderingFilter(SimpleListFilter):
    title = '시간 정렬'
    parameter_name = 'order_by'

    def lookups(self, request, model_admin):
        return [
            ('latest', '최신순'),
            ('oldest', '오래된 순'),
        ]

    def queryset(self, request, queryset):

        if self.value() == 'latest':
            return queryset.order_by('-created_at')

        if self.value() == 'oldest':
            return queryset.order_by('created_at')

        return None # ordering 작동

# 검색 필터
class CustomSearchFilter(SimpleListFilter):
    title = '검색 대상'
    parameter_name = 'search_target'

    def lookups(self, request, model_admin):
        return [
            ('author', '사용자'),
            ('title', '제목'),
            ('content', '내용'),
            ('title_content', '제목 + 내용'),
        ]

    def queryset(self, request, queryset):
        target = self.value()
        query = request.GET.get('q')

        if not query:
            return queryset

        if target == 'author':
            return queryset.filter(author__nickname__icontains=query)

        if target == 'title':
            return queryset.filter(title__icontains=query)

            # '내용만 검색'을 선택했을 때
        if target == 'content':
            return queryset.filter(content__icontains=query)

        if target == 'title_content' or target is None:
            return queryset.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )

        return queryset
