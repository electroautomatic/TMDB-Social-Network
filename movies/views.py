from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Movie, Review
from .forms import MovieSearchForm, ReviewForm, UserRegistrationForm
from .tmdb_api import TMDBApi
from .image_cache import get_or_cache_poster  # Импортируем функцию кэширования


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
    """Home page view that displays popular movies"""
    tmdb_api = TMDBApi()
    popular_movies_data = tmdb_api.get_popular_movies()
    
    movies = []
    if popular_movies_data and 'results' in popular_movies_data:
        # Convert TMDB data to our internal format
        for movie_data in popular_movies_data['results'][:12]:  # Display top 12 movies
            # Save or update the movie in our database
            movie_dict = tmdb_api.format_movie_data(movie_data)
            movie, created = Movie.objects.update_or_create(
                tmdb_id=movie_dict['tmdb_id'],
                defaults=movie_dict
            )
            movies.append(movie)
    
    # Добавляем кэшированные URL постеров к популярным фильмам
    movies = process_movie_posters(movies)
    
    # Also get some movies from our database that have reviews
    local_movies = Movie.objects.annotate(avg_rating=Avg('reviews__rating')).filter(
        reviews__isnull=False
    ).distinct().order_by('-avg_rating')[:6]
    
    # Добавляем кэшированные URL постеров к фильмам с отзывами
    local_movies = process_movie_posters(local_movies)
    
    context = {
        'popular_movies': movies,
        'reviewed_movies': local_movies,
        'search_form': MovieSearchForm()
    }
    return render(request, 'movies/home.html', context)


def search_movies(request):
    """Search for movies using TMDB API"""
    form = MovieSearchForm(request.GET)
    results = []
    
    if form.is_valid():
        query = form.cleaned_data['query']
        tmdb_api = TMDBApi()
        search_results = tmdb_api.search_movies(query)
        
        if search_results and 'results' in search_results:
            # Convert TMDB data to our internal format for display
            for movie_data in search_results['results']:
                movie_dict = tmdb_api.format_movie_data(movie_data)
                # Check if this movie exists in our database
                try:
                    movie = Movie.objects.get(tmdb_id=movie_dict['tmdb_id'])
                except Movie.DoesNotExist:
                    # Create a transient object, but don't save to DB yet
                    movie = Movie(**movie_dict)
                results.append(movie)
    
    # Добавляем кэшированные URL постеров к результатам поиска
    results = process_movie_posters(results)
    
    context = {
        'search_form': form,
        'results': results,
        'query': form.cleaned_data.get('query', '') if form.is_valid() else ''
    }
    return render(request, 'movies/search_results.html', context)


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
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(user=request.user, movie=movie)
        except Review.DoesNotExist:
            pass
    
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
        'is_favorite': request.user.is_authenticated and movie.favorited_by.filter(id=request.user.id).exists()
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
    """Display a user's favorite movies"""
    favorites = request.user.favorite_movies.all()
    
    # Добавляем кэшированные URL постеров
    favorites = process_movie_posters(favorites)
    
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'favorites': page_obj
    }
    return render(request, 'movies/user_favorites.html', context)
