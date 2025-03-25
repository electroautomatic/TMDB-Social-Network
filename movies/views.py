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
    
    # Also get some movies from our database that have reviews
    local_movies = Movie.objects.annotate(avg_rating=Avg('reviews__rating')).filter(
        reviews__isnull=False
    ).distinct().order_by('-avg_rating')[:6]
    
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


@login_required
@require_POST
def toggle_favorite(request, tmdb_id):
    """Toggle whether a movie is in a user's favorites"""
    movie = get_object_or_404(Movie, tmdb_id=tmdb_id)
    
    if movie.favorited_by.filter(id=request.user.id).exists():
        movie.favorited_by.remove(request.user)
        is_favorite = False
    else:
        movie.favorited_by.add(request.user)
        is_favorite = True
    
    return JsonResponse({'status': 'success', 'is_favorite': is_favorite})


@login_required
def user_favorites(request):
    """Display a user's favorite movies"""
    favorites = request.user.favorite_movies.all()
    
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'favorites': page_obj
    }
    return render(request, 'movies/user_favorites.html', context)


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            
            # Auto-login user after registration
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'movies/register.html', {'form': form})
