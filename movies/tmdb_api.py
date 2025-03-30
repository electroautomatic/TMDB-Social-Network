import requests
from django.conf import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TMDBApi:
    """Utility class for interacting with TMDB API"""
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            logger.warning("TMDB API key is not set. Please set it in .env file.")
    
    def _make_request(self, endpoint, params=None):
        """Make a request to TMDB API"""
        if params is None:
            params = {}
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json;charset=utf-8"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to TMDB API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return None
    
    def test_connection(self):
        """Test the connection to TMDB API"""
        endpoint = "/configuration"
        result = self._make_request(endpoint)
        
        if result and 'images' in result:
            return {
                'success': True,
                'message': 'Successfully connected to TMDB API',
                'data': result
            }
        else:
            return {
                'success': False,
                'message': 'Failed to connect to TMDB API. Check your API key and connection.',
                'data': result
            }
    
    def search_movies(self, query, page=1):
        """Search movies by title"""
        endpoint = "/search/movie"
        params = {
            "query": query,
            "page": page
        }
        return self._make_request(endpoint, params)
    
    def get_movie_details(self, movie_id):
        """Get detailed information about a movie"""
        endpoint = f"/movie/{movie_id}"
        return self._make_request(endpoint)
    
    def get_popular_movies(self, page=1):
        """Get list of popular movies"""
        endpoint = "/movie/popular"
        params = {"page": page}
        return self._make_request(endpoint, params)
    
    def get_movie_credits(self, movie_id):
        """Get cast and crew for a movie"""
        endpoint = f"/movie/{movie_id}/credits"
        return self._make_request(endpoint)
    
    def get_similar_movies(self, movie_id, page=1):
        """Get a list of similar movies"""
        endpoint = f"/movie/{movie_id}/similar"
        params = {"page": page}
        return self._make_request(endpoint, params)
    
    # TV SHOWS METHODS
    
    def search_tv_shows(self, query, page=1):
        """Search TV shows by title"""
        endpoint = "/search/tv"
        params = {
            "query": query,
            "page": page
        }
        return self._make_request(endpoint, params)
    
    def get_tv_show_details(self, tv_id):
        """Get detailed information about a TV show"""
        endpoint = f"/tv/{tv_id}"
        return self._make_request(endpoint)
    
    def get_popular_tv_shows(self, page=1):
        """Get list of popular TV shows"""
        endpoint = "/tv/popular"
        params = {"page": page}
        return self._make_request(endpoint, params)
    
    def get_tv_show_credits(self, tv_id):
        """Get cast and crew for a TV show"""
        endpoint = f"/tv/{tv_id}/credits"
        return self._make_request(endpoint)
    
    def get_similar_tv_shows(self, tv_id, page=1):
        """Get a list of similar TV shows"""
        endpoint = f"/tv/{tv_id}/similar"
        params = {"page": page}
        return self._make_request(endpoint, params)
    
    def get_tv_show_seasons(self, tv_id):
        """Get seasons for a TV show"""
        endpoint = f"/tv/{tv_id}"
        result = self._make_request(endpoint)
        if result and 'seasons' in result:
            return result['seasons']
        return []
    
    def get_season_details(self, tv_id, season_number):
        """Get details for a specific season of a TV show"""
        endpoint = f"/tv/{tv_id}/season/{season_number}"
        return self._make_request(endpoint)
    
    def get_episode_details(self, tv_id, season_number, episode_number):
        """Get details for a specific episode of a TV show"""
        endpoint = f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}"
        return self._make_request(endpoint)
    
    def format_movie_data(self, movie_data):
        """Format movie data from TMDB API to match our model"""
        release_date = None
        if movie_data.get('release_date'):
            try:
                release_date = datetime.strptime(movie_data['release_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        return {
            'tmdb_id': movie_data['id'],
            'title': movie_data['title'],
            'overview': movie_data.get('overview', ''),
            'poster_path': movie_data.get('poster_path', ''),
            'release_date': release_date,
            'vote_average': movie_data.get('vote_average', 0),
            'vote_count': movie_data.get('vote_count', 0),
        }
    
    def format_tv_show_data(self, tv_data):
        """Format TV show data from TMDB API to match our model"""
        first_air_date = None
        if tv_data.get('first_air_date'):
            try:
                first_air_date = datetime.strptime(tv_data['first_air_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        return {
            'tmdb_id': tv_data['id'],
            'name': tv_data['name'],
            'overview': tv_data.get('overview', ''),
            'poster_path': tv_data.get('poster_path', ''),
            'first_air_date': first_air_date,
            'vote_average': tv_data.get('vote_average', 0),
            'vote_count': tv_data.get('vote_count', 0),
            'number_of_seasons': tv_data.get('number_of_seasons', 0),
            'number_of_episodes': tv_data.get('number_of_episodes', 0),
            'status': tv_data.get('status', ''),
        }
    
    def format_season_data(self, season_data, tv_show_id):
        """Format season data from TMDB API to match our model"""
        air_date = None
        if season_data.get('air_date'):
            try:
                air_date = datetime.strptime(season_data['air_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        return {
            'tmdb_id': season_data['id'],
            'tv_show_id': tv_show_id,
            'name': season_data['name'],
            'overview': season_data.get('overview', ''),
            'poster_path': season_data.get('poster_path', ''),
            'season_number': season_data.get('season_number', 0),
            'air_date': air_date,
            'episode_count': season_data.get('episode_count', 0),
        }
    
    def format_episode_data(self, episode_data, tv_show_id, season_id):
        """Format episode data from TMDB API to match our model"""
        air_date = None
        if episode_data.get('air_date'):
            try:
                air_date = datetime.strptime(episode_data['air_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        return {
            'tmdb_id': episode_data['id'],
            'tv_show_id': tv_show_id,
            'season_id': season_id,
            'name': episode_data['name'],
            'overview': episode_data.get('overview', ''),
            'still_path': episode_data.get('still_path', ''),
            'episode_number': episode_data.get('episode_number', 0),
            'season_number': episode_data.get('season_number', 0),
            'air_date': air_date,
            'vote_average': episode_data.get('vote_average', 0),
            'vote_count': episode_data.get('vote_count', 0),
        } 