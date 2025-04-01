from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django import forms
from django.urls import reverse

from .models import Movie, Review, TVShow, Season, Episode, TVShowReview, SeasonReview, EpisodeReview
from .models import MovieWatchStatus, TVShowWatchStatus, WatchStatus
from .forms import MovieSearchForm, ReviewForm, UserRegistrationForm, TVShowReviewForm, SeasonReviewForm, EpisodeReviewForm
from .tmdb_api import TMDBApi
from .image_cache import get_or_cache_poster  # Импортируем функцию кэширования
from .models import Friendship, FriendInvitation
from .forms import EmailAuthenticationForm


# Функция-помощник для добавления кэшированных URL изображений
def process_movie_posters(movies_list):
    """
    Обрабатывает список фильмов, заменяя пути к постерам на кэшированные локальные URL.
    
    Args:
        movies_list: Список объектов фильмов (могут быть из БД или из API)
        
    Returns:
        Список фильмов с обновленными путями к постерам
    """
    for movie in movies_list:
        if hasattr(movie, 'poster_path') and movie.poster_path:
            # Получаем кэшированный URL для постера
            cached_url = get_or_cache_poster(movie.poster_path)
            if cached_url:
                # Если у объекта есть метод __dict__, это, вероятно, модель Django
                if hasattr(movie, '__dict__'):
                    movie.cached_poster_url = cached_url
                else:
                    # Иначе, это вероятно словарь из API
                    movie['cached_poster_url'] = cached_url
    
    return movies_list


def home(request):
    """Home page view that displays popular movies and TV shows, and handles search queries"""
    tmdb_api = TMDBApi()
    
    # Проверяем наличие поискового запроса
    form = MovieSearchForm(request.GET)
    movie_results = []
    tvshow_results = []
    search_mode = False
    
    if form.is_valid() and form.cleaned_data.get('query'):
        search_mode = True
        query = form.cleaned_data['query']
        
        # Search for movies
        movie_search_results = tmdb_api.search_movies(query)
        if movie_search_results and 'results' in movie_search_results:
            # Convert TMDB data to our internal format for display
            for movie_data in movie_search_results['results']:
                movie_dict = tmdb_api.format_movie_data(movie_data)
                # Check if this movie exists in our database
                try:
                    movie = Movie.objects.get(tmdb_id=movie_dict['tmdb_id'])
                except Movie.DoesNotExist:
                    # Create a transient object, but don't save to DB yet
                    movie = Movie(**movie_dict)
                movie_results.append(movie)
        
        # Search for TV shows
        tvshow_search_results = tmdb_api.search_tv_shows(query)
        if tvshow_search_results and 'results' in tvshow_search_results:
            # Convert TMDB data to our internal format for display
            for tvshow_data in tvshow_search_results['results']:
                tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
                # Check if this TV show exists in our database
                try:
                    tvshow = TVShow.objects.get(tmdb_id=tvshow_dict['tmdb_id'])
                except TVShow.DoesNotExist:
                    # Create a transient object, but don't save to DB yet
                    tvshow = TVShow(**tvshow_dict)
                tvshow_results.append(tvshow)
                
        # Добавляем кэшированные URL постеров
        movie_results = process_movie_posters(movie_results)
        tvshow_results = process_tvshow_posters(tvshow_results)
    
    # Если нет поискового запроса, отображаем обычную домашнюю страницу
    if not search_mode:
        # Get popular movies
        popular_movies_data = tmdb_api.get_popular_movies()
        
        movies = []
        if popular_movies_data and 'results' in popular_movies_data:
            # Convert TMDB data to our internal format
            for movie_data in popular_movies_data['results'][:8]:  # Display top 8 movies
                # Save or update the movie in our database
                movie_dict = tmdb_api.format_movie_data(movie_data)
                movie, created = Movie.objects.update_or_create(
                    tmdb_id=movie_dict['tmdb_id'],
                    defaults=movie_dict
                )
                movies.append(movie)
        
        # Добавляем кэшированные URL постеров к популярным фильмам
        movies = process_movie_posters(movies)
        
        # Get popular TV shows
        popular_tvshows_data = tmdb_api.get_popular_tv_shows()
        
        tvshows = []
        if popular_tvshows_data and 'results' in popular_tvshows_data:
            # Convert TMDB data to our internal format
            for tvshow_data in popular_tvshows_data['results'][:8]:  # Display top 8 TV shows
                # Save or update the TV show in our database
                tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
                tvshow, created = TVShow.objects.update_or_create(
                    tmdb_id=tvshow_dict['tmdb_id'],
                    defaults=tvshow_dict
                )
                tvshows.append(tvshow)
        
        # Добавляем кэшированные URL постеров к популярным сериалам
        tvshows = process_tvshow_posters(tvshows)
        
        # Also get some movies from our database that have reviews
        local_movies = Movie.objects.annotate(avg_rating=Avg('reviews__rating')).filter(
            reviews__isnull=False
        ).distinct().order_by('-avg_rating')[:4]
        
        # Добавляем кэшированные URL постеров к фильмам с отзывами
        local_movies = process_movie_posters(local_movies)
        
        # Get some TV shows from our database that have reviews
        local_tvshows = TVShow.objects.annotate(avg_rating=Avg('reviews__rating')).filter(
            reviews__isnull=False
        ).distinct().order_by('-avg_rating')[:4]
        
        # Добавляем кэшированные URL постеров к сериалам с отзывами
        local_tvshows = process_tvshow_posters(local_tvshows)
        
        context = {
            'popular_movies': movies,
            'popular_tvshows': tvshows,
            'reviewed_movies': local_movies,
            'reviewed_tvshows': local_tvshows,
            'search_form': MovieSearchForm()
        }
    else:
        # Для поискового режима подготавливаем другой контекст
        context = {
            'search_form': form,
            'movie_results': movie_results,
            'tvshow_results': tvshow_results,
            'query': query if search_mode else '',
            'search_mode': search_mode
        }
    
    # Общий рендеринг для обоих режимов (обычный и поисковый)
    return render(request, 'movies/home.html', context)


def movie_detail(request, tmdb_id):
    """Movie detail view that displays movie information and reviews"""
    # Try to get movie from our database
    try:
        movie = Movie.objects.get(tmdb_id=tmdb_id)
        # Refresh from TMDB
        tmdb_api = TMDBApi()
        movie_data = tmdb_api.get_movie_details(tmdb_id)
        if movie_data:
            movie_dict = tmdb_api.format_movie_data(movie_data)
            for key, value in movie_dict.items():
                setattr(movie, key, value)
            movie.save()
    except Movie.DoesNotExist:
        # Get from TMDB and save to our database
        tmdb_api = TMDBApi()
        movie_data = tmdb_api.get_movie_details(tmdb_id)
        if not movie_data:
            messages.error(request, "Movie not found")
            return redirect('home')
        
        movie_dict = tmdb_api.format_movie_data(movie_data)
        movie = Movie.objects.create(**movie_dict)
    
    # Кэшируем постер фильма
    if movie.poster_path:
        movie.cached_poster_url = get_or_cache_poster(movie.poster_path)
    
    # Get movie reviews
    reviews = movie.reviews.select_related('user').all()
    
    # Check if the current user has already reviewed this movie
    user_review = None
    user_watch_status = None
    is_favorite = False
    
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(user=request.user, movie=movie)
        except Review.DoesNotExist:
            pass
        
        try:
            user_watch_status = MovieWatchStatus.objects.get(user=request.user, movie=movie)
        except MovieWatchStatus.DoesNotExist:
            pass
        
        is_favorite = movie.favorited_by.filter(id=request.user.id).exists()
    
    # Review form
    if request.method == 'POST' and request.user.is_authenticated:
        # Process review form
        form = ReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()
            messages.success(request, "Your review has been saved!")
            return redirect('movie_detail', tmdb_id=tmdb_id)
    else:
        form = ReviewForm(instance=user_review)
    
    context = {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'is_favorite': is_favorite,
        'user_watch_status': user_watch_status,
        'watch_statuses': WatchStatus.choices
    }
    return render(request, 'movies/movie_detail.html', context)


def register(request):
    """Registration view for new users"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'movies/register.html', {'form': form})


@login_required
def add_review(request, tmdb_id):
    """Add or update a review for a movie"""
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    
    if request.method == 'POST':
        # Try to get existing review
        try:
            review = Review.objects.get(user=request.user, movie=movie)
            form = ReviewForm(request.POST, instance=review)
        except Review.DoesNotExist:
            form = ReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()
            messages.success(request, "Your review has been saved!")
        else:
            messages.error(request, "Error in form submission.")
            
    return redirect('movie_detail', tmdb_id=tmdb_id)


@login_required
def delete_review(request, review_id):
    """Delete a review"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect('movie_detail', tmdb_id=review.movie.tmdb_id)


@login_required
def toggle_favorite(request, tmdb_id):
    """Toggle whether a movie is in a user's favorites"""
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    
    if movie.favorited_by.filter(id=request.user.id).exists():
        movie.favorited_by.remove(request.user)
        is_favorite = False
        message = "Movie removed from favorites"
    else:
        movie.favorited_by.add(request.user)
        is_favorite = True
        message = "Movie added to favorites"
    
    # Для AJAX запросов возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'is_favorite': is_favorite, 'message': message})
    
    # Для обычных запросов перенаправляем обратно на страницу фильма
    messages.success(request, message)
    return redirect('movie_detail', tmdb_id=tmdb_id)


@login_required
def user_favorites(request):
    """Display a user's favorite movies and TV shows"""
    # Определяем активную вкладку (по умолчанию - фильмы)
    active_tab = request.GET.get('tab', 'movies')
    
    # Получаем избранные фильмы
    favorite_movies = request.user.favorite_movies.all()
    # Добавляем кэшированные URL постеров к фильмам
    favorite_movies = process_movie_posters(favorite_movies)
    
    # Получаем избранные сериалы
    favorite_tvshows = request.user.favorite_tvshows.all()
    # Добавляем кэшированные URL постеров к сериалам
    favorite_tvshows = process_tvshow_posters(favorite_tvshows)
    
    # Настраиваем пагинацию для фильмов
    movies_paginator = Paginator(favorite_movies, 12)
    movies_page = request.GET.get('page_movies', 1)
    favorite_movies_page = movies_paginator.get_page(movies_page)
    
    # Настраиваем пагинацию для сериалов
    tvshows_paginator = Paginator(favorite_tvshows, 12)
    tvshows_page = request.GET.get('page_tvshows', 1)
    favorite_tvshows_page = tvshows_paginator.get_page(tvshows_page)
    
    context = {
        'favorite_movies': favorite_movies_page,
        'favorite_tvshows': favorite_tvshows_page,
        'active_tab': active_tab
    }
    return render(request, 'movies/user_favorites.html', context)


# TV Shows views
@login_required
def tvshows_home(request):
    """Home page view for TV shows that displays popular TV shows"""
    tmdb_api = TMDBApi()
    popular_tvshows_data = tmdb_api.get_popular_tv_shows()
    
    tvshows = []
    if popular_tvshows_data and 'results' in popular_tvshows_data:
        # Convert TMDB data to our internal format for display
        for tvshow_data in popular_tvshows_data['results'][:12]:  # Display top 12 TV shows
            # Save or update the TV show in our database
            tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
            tvshow, created = TVShow.objects.update_or_create(
                tmdb_id=tvshow_dict['tmdb_id'],
                defaults=tvshow_dict
            )
            tvshows.append(tvshow)
    
    # Добавляем кэшированные URL постеров к популярным сериалам
    tvshows = process_tvshow_posters(tvshows)
    
    # Also get some TV shows from our database that have reviews
    local_tvshows = TVShow.objects.annotate(avg_rating=Avg('reviews__rating')).filter(
        reviews__isnull=False
    ).distinct().order_by('-avg_rating')[:6]
    
    # Добавляем кэшированные URL постеров к сериалам с отзывами
    local_tvshows = process_tvshow_posters(local_tvshows)
    
    context = {
        'popular_tvshows': tvshows,
        'reviewed_tvshows': local_tvshows,
        'search_form': MovieSearchForm()  # Используем такую же форму поиска, как для фильмов
    }
    return render(request, 'movies/tvshows_home.html', context)


def tvshow_detail(request, tmdb_id):
    """TV show detail view that displays TV show information, seasons, episodes and reviews"""
    tmdb_api = TMDBApi()
    
    # Try to get TV show from our database
    try:
        tvshow = TVShow.objects.get(tmdb_id=tmdb_id)
        # Refresh from TMDB
        tvshow_data = tmdb_api.get_tv_show_details(tmdb_id)
        if tvshow_data:
            tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
            for key, value in tvshow_dict.items():
                setattr(tvshow, key, value)
            tvshow.save()
    except TVShow.DoesNotExist:
        # Get from TMDB and save to our database
        tvshow_data = tmdb_api.get_tv_show_details(tmdb_id)
        if not tvshow_data:
            messages.error(request, "TV show not found")
            return redirect('tvshows_home')
        
        tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
        tvshow = TVShow.objects.create(**tvshow_dict)
    
    # Кэшируем постер сериала
    if tvshow.poster_path:
        tvshow.cached_poster_url = get_or_cache_poster(tvshow.poster_path)
    
    # Get seasons using a more reliable approach
    seasons = []
    for season_number in range(1, tvshow.number_of_seasons + 1):
        # Get season data from TMDB first
        season_data = tmdb_api.get_season_details(tmdb_id, season_number)
        if season_data:
            # Format the data
            season_dict = tmdb_api.format_season_data(season_data, tvshow.id)
            
            # Use get_or_create to safely handle the season
            if 'tv_show_id' in season_dict:
                # If tv_show_id is in the dict, we'll use it directly
                defaults = season_dict.copy()
                season, created = Season.objects.get_or_create(
                    tv_show_id=season_dict['tv_show_id'],
                    season_number=season_number,
                    defaults=defaults
                )
            else:
                # If no tv_show_id in the dict, we'll use the tvshow object
                defaults = season_dict.copy()
                season, created = Season.objects.get_or_create(
                    tv_show=tvshow,
                    season_number=season_number,
                    defaults=defaults
                )
            
            # Кэшируем постер сезона
            if season.poster_path:
                season.cached_poster_url = get_or_cache_poster(season.poster_path)
                
            seasons.append(season)
    
    # Get TV show reviews
    reviews = tvshow.reviews.select_related('user').all()
    
    # Check if the current user has already reviewed this TV show
    user_review = None
    user_watch_status = None
    is_favorite = False
    
    if request.user.is_authenticated:
        try:
            user_review = TVShowReview.objects.get(user=request.user, tvshow=tvshow)
        except TVShowReview.DoesNotExist:
            pass
        
        try:
            user_watch_status = TVShowWatchStatus.objects.get(user=request.user, tvshow=tvshow)
        except TVShowWatchStatus.DoesNotExist:
            pass
        
        is_favorite = tvshow.favorited_by.filter(id=request.user.id).exists()
    
    # Review form
    if request.method == 'POST' and request.user.is_authenticated:
        # Process review form
        form = TVShowReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.tvshow = tvshow
            review.save()
            messages.success(request, "Your review has been saved!")
            return redirect('tvshow_detail', tmdb_id=tmdb_id)
    else:
        form = TVShowReviewForm(instance=user_review)
    
    context = {
        'tvshow': tvshow,
        'seasons': seasons,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'is_favorite': is_favorite,
        'user_watch_status': user_watch_status,
        'watch_statuses': WatchStatus.choices
    }
    return render(request, 'movies/tvshow_detail.html', context)


def season_detail(request, tmdb_id, season_number):
    """Season detail view that displays season information, episodes and reviews"""
    tmdb_api = TMDBApi()
    
    # Get TV show
    try:
        tvshow = TVShow.objects.get(tmdb_id=tmdb_id)
    except TVShow.DoesNotExist:
        # Get from TMDB and save to our database
        tvshow_data = tmdb_api.get_tv_show_details(tmdb_id)
        if not tvshow_data:
            messages.error(request, "TV show not found")
            return redirect('tvshows_home')
        
        tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
        tvshow = TVShow.objects.create(**tvshow_dict)
    
    # Get season data from TMDB first, then get or create the season
    season_data = tmdb_api.get_season_details(tmdb_id, season_number)
    if not season_data:
        messages.error(request, "Season not found")
        return redirect('tvshow_detail', tmdb_id=tmdb_id)
    
    # Format the data
    season_dict = tmdb_api.format_season_data(season_data, tvshow.id)
    
    # Use get_or_create to safely handle the season
    if 'tv_show_id' in season_dict:
        # If tv_show_id is in the dict, we'll use it directly
        defaults = season_dict.copy()
        season, created = Season.objects.get_or_create(
            tv_show_id=season_dict['tv_show_id'],
            season_number=season_number,
            defaults=defaults
        )
    else:
        # If no tv_show_id in the dict, we'll use the tvshow object
        defaults = season_dict.copy()
        season, created = Season.objects.get_or_create(
            tv_show=tvshow,
            season_number=season_number,
            defaults=defaults
        )
    
    # Кэшируем постер сезона
    if season.poster_path:
        season.cached_poster_url = get_or_cache_poster(season.poster_path)
    
    # Get episodes
    episodes = []
    season_detail = tmdb_api.get_season_details(tmdb_id, season_number)
    
    if season_detail and 'episodes' in season_detail:
        for episode_data in season_detail['episodes']:
            episode_number = episode_data.get('episode_number')
            
            # Format episode data
            episode_dict = tmdb_api.format_episode_data(episode_data, tvshow.id, season.id)
            
            # Use get_or_create to safely handle the episode
            defaults = episode_dict.copy()
            episode, created = Episode.objects.get_or_create(
                tv_show=tvshow,
                season=season,
                episode_number=episode_number,
                defaults=defaults
            )
            
            # Кэшируем изображение эпизода
            if episode.still_path:
                episode.cached_still_url = get_or_cache_poster(episode.still_path)
                
            episodes.append(episode)
    
    # Get season reviews
    reviews = season.reviews.select_related('user').all()
    
    # Check if the current user has already reviewed this season
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = SeasonReview.objects.get(user=request.user, season=season)
        except SeasonReview.DoesNotExist:
            pass
    
    # Review form
    if request.method == 'POST' and request.user.is_authenticated:
        # Process review form
        form = SeasonReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.season = season
            review.save()
            messages.success(request, "Your review has been saved!")
            return redirect('season_detail', tmdb_id=tmdb_id, season_number=season_number)
    else:
        form = SeasonReviewForm(instance=user_review)
    
    context = {
        'tvshow': tvshow,
        'season': season,
        'episodes': episodes,
        'reviews': reviews,
        'form': form,
        'user_review': user_review
    }
    return render(request, 'movies/season_detail.html', context)


def episode_detail(request, tmdb_id, season_number, episode_number):
    """Episode detail view that displays episode information and reviews"""
    tmdb_api = TMDBApi()
    
    # Get TV show
    try:
        tvshow = TVShow.objects.get(tmdb_id=tmdb_id)
    except TVShow.DoesNotExist:
        # Get from TMDB and save to our database
        tvshow_data = tmdb_api.get_tv_show_details(tmdb_id)
        if not tvshow_data:
            messages.error(request, "TV show not found")
            return redirect('tvshows_home')
        
        tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
        tvshow = TVShow.objects.create(**tvshow_dict)
    
    # Get or create season
    season_data = tmdb_api.get_season_details(tmdb_id, season_number)
    if not season_data:
        messages.error(request, "Season not found")
        return redirect('tvshow_detail', tmdb_id=tmdb_id)
    
    # Format the season data
    season_dict = tmdb_api.format_season_data(season_data, tvshow.id)
    
    # Use get_or_create to safely handle the season
    if 'tv_show_id' in season_dict:
        defaults = season_dict.copy()
        season, created = Season.objects.get_or_create(
            tv_show_id=season_dict['tv_show_id'],
            season_number=season_number,
            defaults=defaults
        )
    else:
        defaults = season_dict.copy()
        season, created = Season.objects.get_or_create(
            tv_show=tvshow,
            season_number=season_number,
            defaults=defaults
        )
    
    # Get or create episode
    episode_data = tmdb_api.get_episode_details(tmdb_id, season_number, episode_number)
    if not episode_data:
        messages.error(request, "Episode not found")
        return redirect('season_detail', tmdb_id=tmdb_id, season_number=season_number)
    
    # Format the episode data
    episode_dict = tmdb_api.format_episode_data(episode_data, tvshow.id, season.id)
    
    # Use get_or_create to safely handle the episode
    defaults = episode_dict.copy()
    episode, created = Episode.objects.get_or_create(
        tv_show=tvshow,
        season=season,
        episode_number=episode_number,
        defaults=defaults
    )
    
    # Кэшируем изображение эпизода
    if episode.still_path:
        episode.cached_still_url = get_or_cache_poster(episode.still_path)
    
    # Get episode reviews
    reviews = episode.reviews.select_related('user').all()
    
    # Check if the current user has already reviewed this episode
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = EpisodeReview.objects.get(user=request.user, episode=episode)
        except EpisodeReview.DoesNotExist:
            pass
    
    # Review form
    if request.method == 'POST' and request.user.is_authenticated:
        # Process review form
        form = EpisodeReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.episode = episode
            review.save()
            messages.success(request, "Your review has been saved!")
            return redirect('episode_detail', tmdb_id=tmdb_id, season_number=season_number, episode_number=episode_number)
    else:
        form = EpisodeReviewForm(instance=user_review)
    
    context = {
        'tvshow': tvshow,
        'season': season,
        'episode': episode,
        'reviews': reviews,
        'form': form,
        'user_review': user_review
    }
    return render(request, 'movies/episode_detail.html', context)


@login_required
def toggle_tvshow_favorite(request, tmdb_id):
    """Toggle whether a TV show is in a user's favorites"""
    tvshow = get_object_or_404(TVShow, tmdb_id=tmdb_id)
    
    if tvshow.favorited_by.filter(id=request.user.id).exists():
        tvshow.favorited_by.remove(request.user)
        is_favorite = False
        message = "TV show removed from favorites"
    else:
        tvshow.favorited_by.add(request.user)
        is_favorite = True
        message = "TV show added to favorites"
    
    # Для AJAX запросов возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'is_favorite': is_favorite, 'message': message})
    
    # Для обычных запросов перенаправляем обратно на страницу сериала
    messages.success(request, message)
    return redirect('tvshow_detail', tmdb_id=tmdb_id)


# Helper function for TV shows
def process_tvshow_posters(tvshows_list):
    """
    Обрабатывает список сериалов, заменяя пути к постерам на кэшированные локальные URL.
    
    Args:
        tvshows_list: Список объектов сериалов (могут быть из БД или из API)
        
    Returns:
        Список сериалов с обновленными путями к постерам
    """
    for tvshow in tvshows_list:
        if hasattr(tvshow, 'poster_path') and tvshow.poster_path:
            # Получаем кэшированный URL для постера
            cached_url = get_or_cache_poster(tvshow.poster_path)
            if cached_url:
                # Если у объекта есть метод __dict__, это, вероятно, модель Django
                if hasattr(tvshow, '__dict__'):
                    tvshow.cached_poster_url = cached_url
                else:
                    # Иначе, это вероятно словарь из API
                    tvshow['cached_poster_url'] = cached_url
    
    return tvshows_list


@require_POST
@login_required
def add_tvshow_to_favorites(request):
    """Add TV show to user favorites via AJAX"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseBadRequest("Invalid request")
    
    tmdb_id = request.POST.get('tmdb_id')
    action = request.POST.get('action', 'add')
    
    tmdb_api = TMDBApi()
    
    # Handle removing from favorites
    if action == 'remove':
        try:
            tvshow = TVShow.objects.get(tmdb_id=tmdb_id)
            tvshow.favorited_by.remove(request.user)
            return JsonResponse({'status': 'success', 'message': 'Removed from favorites'})
        except TVShow.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'TV show not found'})
    
    # Try to get the TV show from our database first
    try:
        tvshow = TVShow.objects.get(tmdb_id=tmdb_id)
    except TVShow.DoesNotExist:
        # Get from TMDB and save to our database
        tvshow_data = tmdb_api.get_tv_show_details(tmdb_id)
        if not tvshow_data:
            return JsonResponse({'status': 'error', 'message': 'TV show not found'})
        
        tvshow_dict = tmdb_api.format_tv_show_data(tvshow_data)
        tvshow = TVShow.objects.create(**tvshow_dict)
    
    # Check if already a favorite
    already_favorite = tvshow.favorited_by.filter(id=request.user.id).exists()
    
    if not already_favorite:
        # Add to favorites
        tvshow.favorited_by.add(request.user)
        message = 'Added to favorites'
    else:
        message = 'Already in favorites'
    
    return JsonResponse({'status': 'success', 'message': message})


@login_required
@require_POST
def set_movie_watch_status(request, tmdb_id):
    """Set the watch status for a movie"""
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    
    # Get status from POST data
    status = request.POST.get('status')
    is_rewatching = request.POST.get('is_rewatching') == 'true'
    
    # Validate status
    if status not in [choice[0] for choice in WatchStatus.choices]:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)
    
    # Get or create status object
    watch_status, created = MovieWatchStatus.objects.get_or_create(
        user=request.user,
        movie=movie,
        defaults={'status': status, 'is_rewatching': is_rewatching}
    )
    
    if not created:
        # Update existing status
        watch_status.status = status
        watch_status.is_rewatching = is_rewatching
        watch_status.save()
    
    # Return response
    status_text = dict(WatchStatus.choices)[status]
    message = f"Movie marked as '{status_text}'"
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'message': message,
            'watch_status': status,
            'is_rewatching': is_rewatching
        })
    
    # For regular requests
    messages.success(request, message)
    return redirect('movie_detail', tmdb_id=tmdb_id)


@login_required
@require_POST
def set_tvshow_watch_status(request, tmdb_id):
    """Set the watch status for a TV show"""
    tvshow = get_object_or_404(TVShow, tmdb_id=tmdb_id)
    
    # Get status from POST data
    status = request.POST.get('status')
    is_rewatching = request.POST.get('is_rewatching') == 'true'
    
    # Validate status
    if status not in [choice[0] for choice in WatchStatus.choices]:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)
    
    # Get or create status object
    watch_status, created = TVShowWatchStatus.objects.get_or_create(
        user=request.user,
        tvshow=tvshow,
        defaults={'status': status, 'is_rewatching': is_rewatching}
    )
    
    if not created:
        # Update existing status
        watch_status.status = status
        watch_status.is_rewatching = is_rewatching
        watch_status.save()
    
    # Return response
    status_text = dict(WatchStatus.choices)[status]
    message = f"TV show marked as '{status_text}'"
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'message': message,
            'watch_status': status,
            'is_rewatching': is_rewatching
        })
    
    # For regular requests
    messages.success(request, message)
    return redirect('tvshow_detail', tmdb_id=tmdb_id)


@login_required
def my_watch_list(request):
    """Display a user's watch list organized by status"""
    # Get the active tab from the query string
    active_tab = request.GET.get('tab', 'movies')
    active_status = request.GET.get('status', 'want_to_watch')
    
    # Movies by status
    movie_statuses = MovieWatchStatus.objects.filter(user=request.user)
    
    # Get all favorite movie IDs for the user
    favorite_movie_ids = request.user.favorite_movies.values_list('id', flat=True)
    
    # Create dictionaries to store movies by status
    movies_by_status = {
        'want_to_watch': [],
        'watching': [],
        'on_hold': [],
        'completed': [],
        'dropped': []
    }
    
    # Sort movies into their status categories
    for movie_status in movie_statuses:
        movies_by_status[movie_status.status].append({
            'movie': movie_status.movie,
            'is_rewatching': movie_status.is_rewatching,
            'is_favorite': movie_status.movie.id in favorite_movie_ids
        })
    
    # Process posters for all movies
    for status, movies in movies_by_status.items():
        for item in movies:
            if item['movie'].poster_path:
                item['movie'].cached_poster_url = get_or_cache_poster(item['movie'].poster_path)
    
    # TV Shows by status
    tvshow_statuses = TVShowWatchStatus.objects.filter(user=request.user)
    
    # Get all favorite TV show IDs for the user
    favorite_tvshow_ids = request.user.favorite_tvshows.values_list('id', flat=True)
    
    # Create dictionaries to store TV shows by status
    tvshows_by_status = {
        'want_to_watch': [],
        'watching': [],
        'on_hold': [],
        'completed': [],
        'dropped': []
    }
    
    # Sort TV shows into their status categories
    for tvshow_status in tvshow_statuses:
        tvshows_by_status[tvshow_status.status].append({
            'tvshow': tvshow_status.tvshow,
            'is_rewatching': tvshow_status.is_rewatching,
            'is_favorite': tvshow_status.tvshow.id in favorite_tvshow_ids
        })
    
    # Process posters for all TV shows
    for status, tvshows in tvshows_by_status.items():
        for item in tvshows:
            if item['tvshow'].poster_path:
                item['tvshow'].cached_poster_url = get_or_cache_poster(item['tvshow'].poster_path)
    
    # Context data for template
    context = {
        'active_tab': active_tab,
        'active_status': active_status,
        'movies_by_status': movies_by_status,
        'tvshows_by_status': tvshows_by_status,
        'statuses': WatchStatus.choices
    }
    
    return render(request, 'movies/my_watch_list.html', context)


# Friend-related views
@login_required
def my_friends(request):
    """Отображает список друзей пользователя и форму для создания приглашения"""
    # Получаем список друзей пользователя
    user_friendships = Friendship.objects.filter(user=request.user).select_related('friend')
    friends = [friendship.friend for friendship in user_friendships]
    
    # Проверяем, есть ли у пользователя активное приглашение
    from django.utils import timezone
    active_invitation = FriendInvitation.objects.filter(
        creator=request.user,
        expires_at__gt=timezone.now(),
        uses_remaining__gt=0
    ).first()
    
    # Создаем приглашение, если нужно
    invitation_url = None
    if active_invitation:
        invitation_url = request.build_absolute_uri(
            reverse('accept_friend_invitation', args=[active_invitation.token])
        )
    
    context = {
        'friends': friends,
        'active_invitation': active_invitation,
        'invitation_url': invitation_url
    }
    
    return render(request, 'movies/my_friends.html', context)

@login_required
def create_friend_invitation(request):
    """Создает новое приглашение дружбы"""
    if request.method == 'POST':
        # Проверяем, есть ли у пользователя активное приглашение, и удаляем его
        from django.utils import timezone
        FriendInvitation.objects.filter(creator=request.user).delete()
        
        # Создаем новое приглашение
        import uuid
        import datetime
        token = uuid.uuid4().hex
        expires_at = timezone.now() + datetime.timedelta(days=7)  # Срок действия 7 дней
        
        invitation = FriendInvitation.objects.create(
            creator=request.user,
            token=token,
            uses_remaining=3,  # Ссылка действует только 3 раза
            expires_at=expires_at
        )
        
        # Формируем URL приглашения
        invitation_url = request.build_absolute_uri(
            reverse('accept_friend_invitation', args=[token])
        )
        
        # Возвращаем URL в формате JSON при AJAX-запросе
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'invitation_url': invitation_url
            })
        
        messages.success(request, "Invitation link has been created!")
        return redirect('my_friends')
    
    # Если это не POST-запрос, перенаправляем на страницу друзей
    return redirect('my_friends')

def accept_friend_invitation(request, token):
    """Обрабатывает принятие приглашения по ссылке"""
    # Проверяем существование и действительность приглашения
    from django.utils import timezone
    invitation = get_object_or_404(
        FriendInvitation,
        token=token,
        expires_at__gt=timezone.now(),
        uses_remaining__gt=0
    )
    
    # Если пользователь не аутентифицирован, перенаправляем на регистрацию с сохранением токена
    if not request.user.is_authenticated:
        messages.info(request, "Please register or login to accept the friend invitation")
        return redirect(f"/register/?invitation_token={token}")
    
    # Проверяем, не является ли пользователь создателем приглашения
    if invitation.creator == request.user:
        messages.warning(request, "You cannot add yourself as a friend")
        return redirect('my_friends')
    
    # Проверяем, есть ли уже такая дружба
    friendship_exists = Friendship.objects.filter(
        user=invitation.creator,
        friend=request.user
    ).exists() or Friendship.objects.filter(
        user=request.user,
        friend=invitation.creator
    ).exists()
    
    if not friendship_exists:
        # Создаем двустороннюю дружбу (взаимная)
        Friendship.objects.create(user=invitation.creator, friend=request.user)
        Friendship.objects.create(user=request.user, friend=invitation.creator)
        
        # Уменьшаем количество оставшихся использований инвайта
        invitation.uses_remaining -= 1
        invitation.save()
        
        messages.success(request, f"You are now friends with {invitation.creator.username}!")
    else:
        messages.info(request, f"You are already friends with {invitation.creator.username}")
    
    return redirect('my_friends')

@login_required
def friend_watch_list(request, friend_id):
    """Отображает списки фильмов и сериалов друга"""
    # Проверяем, является ли пользователь другом
    friendship = get_object_or_404(
        Friendship, 
        user=request.user, 
        friend_id=friend_id
    )
    
    friend = friendship.friend
    
    # Получаем параметры фильтрации
    active_tab = request.GET.get('tab', 'movies')  # По умолчанию, вкладка фильмов
    active_status = request.GET.get('status', WatchStatus.COMPLETED)  # По умолчанию, завершенные
    
    # Подготавливаем словари для хранения статусов фильмов и сериалов
    movies_by_status = {status[0]: [] for status in WatchStatus.choices}
    tvshows_by_status = {status[0]: [] for status in WatchStatus.choices}
    
    # Получаем статусы фильмов друга
    movie_statuses = MovieWatchStatus.objects.filter(user=friend).select_related('movie')
    for status in movie_statuses:
        is_favorite = status.movie.favorited_by.filter(id=friend.id).exists()
        movies_by_status[status.status].append({
            'movie': status.movie,
            'status': status.status,
            'is_rewatching': status.is_rewatching,
            'is_favorite': is_favorite
        })
    
    # Получаем статусы сериалов друга
    tvshow_statuses = TVShowWatchStatus.objects.filter(user=friend).select_related('tvshow')
    for status in tvshow_statuses:
        is_favorite = status.tvshow.favorited_by.filter(id=friend.id).exists()
        tvshows_by_status[status.status].append({
            'tvshow': status.tvshow,
            'status': status.status,
            'is_rewatching': status.is_rewatching,
            'is_favorite': is_favorite
        })
    
    # Добавляем кэшированные URL постеров
    for status in WatchStatus.choices:
        status_code = status[0]
        for item in movies_by_status[status_code]:
            if item['movie'].poster_path:
                item['movie'].cached_poster_url = get_or_cache_poster(item['movie'].poster_path)
        
        for item in tvshows_by_status[status_code]:
            if item['tvshow'].poster_path:
                item['tvshow'].cached_poster_url = get_or_cache_poster(item['tvshow'].poster_path)
    
    context = {
        'friend': friend,
        'active_tab': active_tab,
        'active_status': active_status,
        'statuses': WatchStatus.choices,
        'movies_by_status': movies_by_status,
        'tvshows_by_status': tvshows_by_status
    }
    
    return render(request, 'movies/friend_watch_list.html', context)

def login_view(request):
    """Custom login view that uses email authentication"""
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Перенаправление на страницу, с которой пользователь пришел
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'movies/login.html', {'form': form})
