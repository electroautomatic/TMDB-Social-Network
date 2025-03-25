"""
URL configuration for tmdb_net project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from movies.admin import TMDBApiAdmin
from movies.models import Movie

# Создаем экземпляр TMDBApiAdmin для использования его представлений
tmdb_admin = TMDBApiAdmin()

urlpatterns = [
    # Добавляем URL-паттерны для TMDB API тестирования
    # Эти маршруты должны быть определены ДО admin.site.urls
    path('admin/test-api-connection/', tmdb_admin.test_api_connection_view, name='admin-test-tmdb-api'),
    path('admin/test-api-connection/check/', tmdb_admin.check_api_connection, name='admin-check-tmdb-api'),
    path('admin/test-api-popular/', tmdb_admin.test_popular_movies, name='admin-test-popular-movies'),
    
    # Основные маршруты админки
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='movies/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Include movies app URLs
    path('', include('movies.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
