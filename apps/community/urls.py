from django.urls import URLPattern, URLResolver, path

from apps.community.admin import community_admin_site

urlpatterns: list[URLPattern | URLResolver] = [path("admin/", community_admin_site.urls)]
