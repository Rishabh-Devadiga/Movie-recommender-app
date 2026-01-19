import requests
import time
import pandas as pd

# Get API key from Streamlit secrets (will be None if not set)
try:
    import streamlit as st
    API_KEY = st.secrets.get('TMDB_API_KEY')
except:
    API_KEY = None  # For standalone script

# Improved safe_get function
def safe_get(url, retries=3, delay=2):
    for i in range(retries):
        try:
            print(f"Attempting to fetch data from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            print("Data fetched successfully.")
            return response
        except requests.exceptions.ConnectionError as e:
            print(f"ConnectionError: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
        except requests.exceptions.HTTPError as e:
            print(f"HTTPError: {e}. Status code: {response.status_code}")
            break
        except requests.exceptions.Timeout as e:
            print(f"TimeoutError: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
        except requests.exceptions.RequestException as e:
            print(f"⚠ Request failed: {e}")
            break
    print("Failed to fetch data after several attempts.")
    return None

# Create a function to generate the movies CSV
def create_movies_csv(api_key=None):
    if api_key is None:
        try:
            import streamlit as st
            api_key = st.secrets.get('TMDB_API_KEY')
        except:
            api_key = None
    if not api_key:
        print("⚠️ TMDB API key is required to create the movies database.")
        return None
    movies_data = []
    max_movies = 500  # Limit to 500 movies to keep database manageable
    try:
        for page in range(1, 6):  # Fetch pages 1 to 5 (100 movies per page, but we'll limit)
            if len(movies_data) >= max_movies:
                break
            # Fetch popular movies from TMDB
            url = f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page={page}'
            response = safe_get(url)
            if response and response.status_code == 200:
                data = response.json()
                for movie in data['results']:
                    if len(movies_data) >= max_movies:
                        break
                    # Get detailed movie info
                    movie_id = movie['id']
                    details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
                    details_response = safe_get(details_url)
                    
                    if details_response and details_response.status_code == 200:
                        details = details_response.json()
                        movies_data.append({
                            'id': movie_id,
                            'title': movie['title'],
                            'overview': movie['overview'],
                            'genres': ' '.join([genre['name'] for genre in details.get('genres', [])]),
                            'poster_path': movie['poster_path'],
                            'release_date': movie['release_date'],
                            'vote_average': movie['vote_average']
                        })
                    time.sleep(0.5)  # Be nice to TMDB API
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(movies_data)
        df.to_csv('movies.csv', index=False)
        return df
    except Exception as e:
        print(f"Error creating movies database: {str(e)}")
        return None