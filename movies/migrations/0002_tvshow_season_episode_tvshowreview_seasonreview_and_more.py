# Generated by Django 4.2.7 on 2025-03-30 18:08

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TVShow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('poster_path', models.CharField(blank=True, max_length=255, null=True)),
                ('first_air_date', models.DateField(blank=True, null=True)),
                ('vote_average', models.FloatField(default=0)),
                ('vote_count', models.IntegerField(default=0)),
                ('number_of_seasons', models.IntegerField(default=0)),
                ('number_of_episodes', models.IntegerField(default=0)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('favorited_by', models.ManyToManyField(blank=True, related_name='favorite_tvshows', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'TV Show',
                'verbose_name_plural': 'TV Shows',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('poster_path', models.CharField(blank=True, max_length=255, null=True)),
                ('season_number', models.IntegerField()),
                ('air_date', models.DateField(blank=True, null=True)),
                ('episode_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tv_show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='movies.tvshow')),
            ],
            options={
                'ordering': ['season_number'],
                'unique_together': {('tv_show', 'season_number')},
            },
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('still_path', models.CharField(blank=True, max_length=255, null=True)),
                ('episode_number', models.IntegerField()),
                ('season_number', models.IntegerField()),
                ('air_date', models.DateField(blank=True, null=True)),
                ('vote_average', models.FloatField(default=0)),
                ('vote_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='movies.season')),
                ('tv_show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='movies.tvshow')),
            ],
            options={
                'ordering': ['season_number', 'episode_number'],
                'unique_together': {('tv_show', 'season_number', 'episode_number')},
            },
        ),
        migrations.CreateModel(
            name='TVShowReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Rating must be at least 1'), django.core.validators.MaxValueValidator(10, message='Rating cannot be higher than 10')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tvshow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='movies.tvshow')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tvshow_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'TV Show Review',
                'verbose_name_plural': 'TV Show Reviews',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'tvshow')},
            },
        ),
        migrations.CreateModel(
            name='SeasonReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Rating must be at least 1'), django.core.validators.MaxValueValidator(10, message='Rating cannot be higher than 10')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='movies.season')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='season_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('user', 'season')},
            },
        ),
        migrations.CreateModel(
            name='EpisodeReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Rating must be at least 1'), django.core.validators.MaxValueValidator(10, message='Rating cannot be higher than 10')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='movies.episode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episode_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('user', 'episode')},
            },
        ),
    ]
