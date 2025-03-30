from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Movie(models.Model):
    """Model for storing movie data from TMDB API"""
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    vote_average = models.FloatField(default=0)
    vote_count = models.IntegerField(default=0)
    favorited_by = models.ManyToManyField(User, related_name='favorite_movies', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    """Model for user reviews of movies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(10, message="Rating cannot be higher than 10")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review of {self.movie.title}"


# TV Shows models
class TVShow(models.Model):
    """Model for storing TV show data from TMDB API"""
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    first_air_date = models.DateField(blank=True, null=True)
    vote_average = models.FloatField(default=0)
    vote_count = models.IntegerField(default=0)
    number_of_seasons = models.IntegerField(default=0)
    number_of_episodes = models.IntegerField(default=0)
    status = models.CharField(max_length=50, blank=True, null=True)
    favorited_by = models.ManyToManyField(User, related_name='favorite_tvshows', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = "TV Show"
        verbose_name_plural = "TV Shows"


class Season(models.Model):
    """Model for storing TV show season data from TMDB API"""
    tmdb_id = models.IntegerField()
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='seasons')
    name = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    season_number = models.IntegerField()
    air_date = models.DateField(blank=True, null=True)
    episode_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tv_show.name} - {self.name}"

    class Meta:
        ordering = ['season_number']
        unique_together = ('tv_show', 'season_number')


class Episode(models.Model):
    """Model for storing TV show episode data from TMDB API"""
    tmdb_id = models.IntegerField()
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='episodes')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    name = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    still_path = models.CharField(max_length=255, blank=True, null=True)
    episode_number = models.IntegerField()
    season_number = models.IntegerField()
    air_date = models.DateField(blank=True, null=True)
    vote_average = models.FloatField(default=0)
    vote_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tv_show.name} - S{self.season_number:02d}E{self.episode_number:02d} - {self.name}"

    class Meta:
        ordering = ['season_number', 'episode_number']
        unique_together = ('tv_show', 'season_number', 'episode_number')


class TVShowReview(models.Model):
    """Model for user reviews of TV shows"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tvshow_reviews')
    tvshow = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(10, message="Rating cannot be higher than 10")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'tvshow')
        ordering = ['-created_at']
        verbose_name = "TV Show Review"
        verbose_name_plural = "TV Show Reviews"

    def __str__(self):
        return f"{self.user.username}'s review of {self.tvshow.name}"


class SeasonReview(models.Model):
    """Model for user reviews of TV show seasons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='season_reviews')
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(10, message="Rating cannot be higher than 10")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'season')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review of {self.season.tv_show.name} - {self.season.name}"


class EpisodeReview(models.Model):
    """Model for user reviews of TV show episodes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='episode_reviews')
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message="Rating must be at least 1"),
            MaxValueValidator(10, message="Rating cannot be higher than 10")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'episode')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review of {self.episode.tv_show.name} - S{self.episode.season_number:02d}E{self.episode.episode_number:02d}"
