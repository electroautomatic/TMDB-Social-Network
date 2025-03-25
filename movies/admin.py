from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from .models import Movie, Review
from .tmdb_api import TMDBApi
from django.utils.html import format_html


class APILinkMixin:
    def api_test_link(self, obj):
        return format_html('<a href="/admin/test-api-connection/">Проверить подключение к TMDB API</a>')
    api_test_link.short_description = "API Test"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin, APILinkMixin):
    list_display = ('title', 'tmdb_id', 'release_date', 'vote_average', 'created_at', 'api_test_link')
    search_fields = ('title', 'tmdb_id')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('tmdb_id', 'created_at', 'updated_at', 'api_test_link')
    filter_horizontal = ('favorited_by',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin, APILinkMixin):
    list_display = ('user', 'movie', 'rating', 'created_at', 'api_test_link')
    search_fields = ('user__username', 'movie__title')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'api_test_link')


# Custom admin for TMDB API testing
class TMDBApiAdmin:
    """
    Класс для тестирования TMDB API в админке.
    URL-маршруты определены в tmdb_net/urls.py
    """
    def test_api_connection_view(self, request):
        context = {
            'title': 'Test TMDB API Connection',
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'api_key': '*' * 8 + TMDBApi().api_key[-5:] if TMDBApi().api_key else None,
        }
        return TemplateResponse(request, 'admin/tmdb_api_test.html', context)
    
    def check_api_connection(self, request):
        api = TMDBApi()
        result = api.test_connection()
        return JsonResponse(result)
    
    def test_popular_movies(self, request):
        api = TMDBApi()
        result = api.get_popular_movies()
        if result and 'results' in result:
            return JsonResponse({
                'success': True,
                'message': f'Successfully retrieved {len(result["results"])} popular movies',
                'results': result['results'][:5]  # Limiting to 5 movies for display
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to retrieve popular movies',
                'data': result
            })


# Настраиваем шаблон главной страницы админки
admin.site.index_template = 'admin/custom_index.html'
