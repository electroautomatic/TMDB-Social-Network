# TMDB Social Network

A Django web application that serves as a social network for movie enthusiasts. Users can register, save their favorite movies, write reviews, rate movies, and get movie information from TMDB API.

## Features

- User registration and authentication
- Adding movies to favorites list
- Writing reviews and rating movies
- Viewing movie ratings from other users
- Fetching movie data from TMDB API

## Tech Stack

- **Backend**: Django 
- **Database**: PostgreSQL (Docker) / SQLite (local development)
- **Database Management**: Adminer
- **Frontend**: Bootstrap 5 with Django Templates
- **API Integration**: TMDB API

## Prerequisites

- Docker and Docker Compose (for production setup)
- Python 3.9+ (for local development)

## Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tmdb_net
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy the `.env.example` file to `.env` and set your TMDB API key
   - Make sure `USE_SQLITE=True` is set for local development

4. Apply migrations and run the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### Docker Setup

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Access the application:
   - Web App: http://localhost:8000
   - Database Admin (Adminer): http://localhost:8080
     - System: PostgreSQL
     - Server: db
     - Username: tmdb_user (or as configured in .env)
     - Password: tmdb_password (or as configured in .env)
     - Database: tmdb_db (or as configured in .env)

## API Integration

The application uses TMDB API to fetch movie data. You need to get an API key from [TMDB](https://www.themoviedb.org/documentation/api) and set it in the `.env` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details. # TMDB-Social-Network
