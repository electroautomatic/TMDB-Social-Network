from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<int:tmdb_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:tmdb_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('movie/<int:tmdb_id>/review/', views.add_review, name='add_review'),
    path('movie/<int:tmdb_id>/watch-status/', views.set_movie_watch_status, name='set_movie_watch_status'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('favorites/', views.user_favorites, name='user_favorites'),
    path('register/', views.register, name='register'),
    
    path('tvshows/', views.tvshows_home, name='tvshows_home'),
    path('tvshow/<int:tmdb_id>/', views.tvshow_detail, name='tvshow_detail'),
    path('tvshow/<int:tmdb_id>/favorite/', views.toggle_tvshow_favorite, name='toggle_tvshow_favorite'),
    path('tvshow/<int:tmdb_id>/watch-status/', views.set_tvshow_watch_status, name='set_tvshow_watch_status'),
    path('tvshow/<int:tmdb_id>/season/<int:season_number>/', views.season_detail, name='season_detail'),
    path('tvshow/<int:tmdb_id>/season/<int:season_number>/episode/<int:episode_number>/', views.episode_detail, name='episode_detail'),
    
    path('my-list/', views.my_watch_list, name='my_watch_list'),
    
    # Friend-related URLs
    path('my-friends/', views.my_friends, name='my_friends'),
    path('friends/create-invitation/', views.create_friend_invitation, name='create_friend_invitation'),
    path('friends/accept-invitation/<str:token>/', views.accept_friend_invitation, name='accept_friend_invitation'),
    path('friends/view/<int:friend_id>/', views.friend_watch_list, name='friend_watch_list'),
    path('friends/favorites/<int:friend_id>/', views.friend_favorites, name='friend_favorites'),
] 