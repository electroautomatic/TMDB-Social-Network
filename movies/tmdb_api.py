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