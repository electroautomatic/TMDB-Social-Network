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
from movies.views import login_view

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
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='movies/password_reset_form.html',
        email_template_name='movies/password_reset_email.html',
        subject_template_name='movies/password_reset_subject.txt',
        success_url='/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='movies/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='movies/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='movies/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Include movies app URLs
    path('', include('movies.urls')),
]

# Serve media files in development ONLY
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
