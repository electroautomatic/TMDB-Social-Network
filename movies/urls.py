from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:tmdb_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('movie/<int:tmdb_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('favorites/', views.user_favorites, name='user_favorites'),
    path('register/', views.register, name='register'),
    
    path('tvshows/', views.tvshows_home, name='tvshows_home'),
    path('tvshow/<int:tmdb_id>/', views.tvshow_detail, name='tvshow_detail'),
    path('tvshow/<int:tmdb_id>/favorite/', views.toggle_tvshow_favorite, name='toggle_tvshow_favorite'),
    path('tvshow/<int:tmdb_id>/season/<int:season_number>/', views.season_detail, name='season_detail'),
    path('tvshow/<int:tmdb_id>/season/<int:season_number>/episode/<int:episode_number>/', views.episode_detail, name='episode_detail'),
] 