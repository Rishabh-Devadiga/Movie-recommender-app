import streamlit as st
import requests
import time 
import socket
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('TMDB_API_KEY')
if not API_KEY:
    st.error("⚠️ TMDB API key not found. Please set the TMDB_API_KEY environment variable.")
    st.stop()

st.write("✅ App started")

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

# Theme Toggle
use_light_mode = st.toggle("☀ Light Mode", value=False)
st.session_state["dark_mode"] = not use_light_mode 

if use_light_mode:
    st.markdown(
       """
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
            background-color: #ffffff !important;
            color: #000000 !important;
            transition: background-color 0.5s ease, color 0.5s ease;
        }

        [data-testid="stHeader"] {
            background-color: #ffffff !important;
        }

        .block-container {
            background-color: #ffffff !important;
            color: #000000 !important;
        }

        .stButton>button {
            background-color: #e1e1e1 !important;
            color: #000000 !important;
        }

        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #000000 !important;
        }
        </style>
        """,
   unsafe_allow_html = True
        )
else:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .stApp {
            background-color: #181818 !important;
            color: #ffffff !important;
            transition: background-color 0.5s ease, color 0.5s ease;
        }
        [data-testid="stHeader"] {
            background-color: #181818 !important;
        }
        .block-container {
            background-color: #181818 !important;
            color: #ffffff !important;
        }
        .stButton>button {
            background-color: #333333 !important;
            color: #ffffff !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

#Streamlit UI 
st.title("📽 Movie Recommendor")

# Initialize session state variables
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "current_recommendations" not in st.session_state:
    st.session_state.current_recommendations = []
if "last_searched_movie" not in st.session_state:
    st.session_state.last_searched_movie = None

# Function to add movie to watchlist
def add_to_watchlist(movie):
    titles_in_watchlist = [m['title'] for m in st.session_state.watchlist]
    if movie['title'] not in titles_in_watchlist:
        st.session_state.watchlist.append(movie.copy())
        return True
    return False

# Create a function to generate the movies CSV
def create_movies_csv():
    movies_data = []
    try:
        # Fetch popular movies from TMDB
        url = f'https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page=1'
        response = safe_get(url)
        if response and response.status_code == 200:
            data = response.json()
            for movie in data['results'][:100]:  # Get first 100 movies
                # Get detailed movie info
                movie_id = movie['id']
                details_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}'
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
        st.error(f"Error creating movies database: {str(e)}")
        return None

# Function to get movie recommendations based on content similarity
def get_content_based_recommendations(movie_title, n_recommendations=5):
    try:
        # Read the movies database
        df = pd.read_csv('movies.csv')
        
        # Fill NaN values with empty strings
        df['overview'] = df['overview'].fillna('')
        df['genres'] = df['genres'].fillna('')
        # Combine relevant features for similarity
        df['combined_features'] = df['overview'] + ' ' + df['genres']
        
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['combined_features'])
        
        # Calculate cosine similarity
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        # Get the index of the movie (case-insensitive match)
        matches = df[df['title'].str.lower() == movie_title.lower()]
        if matches.empty:
            st.error(f"Movie '{movie_title}' not found in the database. Try another title!")
            return []
        idx = matches.index[0]
        
        # Get similarity scores
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:n_recommendations+1]  # Skip the first one (same movie)
        
        # Get movie indices
        movie_indices = [i[0] for i in sim_scores]
        
        # Return recommended movies
        recommendations = []
        for idx in movie_indices:
            movie = df.iloc[idx]
            recommendations.append({
                'title': movie['title'],
                'overview': movie['overview'],
                'poster_url': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else None,
                'genres': movie['genres'],
                'vote_average': movie['vote_average']
            })
        
        return recommendations
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return []

# Initialize movies database if it doesn't exist
if not os.path.exists('movies.csv'):
    with st.spinner("Creating movies database..."):
        create_movies_csv()

# Clear watchlist button
if st.button("Clear Watchlist"):
    st.session_state.watchlist = []
    st.success("Watchlist cleared!")

st.write("Type your favourite movies and get similar recommendations!")

# Movie search section
movie_query = st.text_input("Enter a movie name: ")

selected_movie = None
if movie_query:
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_query}"
    response = safe_get(url)
    if not response:
        st.error("⚠ Failed to fetch data from TMDB after several attempts.")
        st.stop()
    
    if response.status_code == 200:
        results = response.json().get("results", [])
        movie_options = [movie["title"] for movie in results[:5]]
        if movie_options:
            selected_movie = st.selectbox("Did you mean:", movie_options)
        else:
            st.write("🔍 No matching movies found.")

# Get recommendations when button is clicked
if selected_movie and st.button("Get Recommendations"):
    with st.spinner("📽 Finding similar movies..."):
        recommendations = get_content_based_recommendations(selected_movie)
        if recommendations:
            st.session_state.current_recommendations = recommendations
            st.session_state.last_searched_movie = selected_movie
        else:
            st.session_state.current_recommendations = []
    st.success("✔ Done!")

# Display recommendations section
if st.session_state.current_recommendations:
    st.subheader(f"Movies similar to {st.session_state.last_searched_movie}:")
    for idx, sim_movie in enumerate(st.session_state.current_recommendations):
        with st.container():
            st.markdown(f"### 📽  {sim_movie['title']}")
            cols = st.columns([1,3,1])

            with cols[0]:
                if sim_movie['poster_url']:
                    st.image(sim_movie['poster_url'], width=150)
            
            with cols[1]:
                if sim_movie['overview']:
                    st.write(f"### 📚  {sim_movie['overview']}")
                st.write(f"**Genres:** {sim_movie['genres']}")
                st.write(f"**Rating:** ⭐ {sim_movie['vote_average']}/10")
            
            with cols[2]:
                button_key = f"watchlist_{idx}_{sim_movie['title']}"
                if st.button("➕ Add to watchlist", key=button_key):
                    if add_to_watchlist(sim_movie):
                        st.success(f"✅ {sim_movie['title']} added to watchlist!")
                    else:
                        st.info(f"{sim_movie['title']} is already in your watchlist.")
            
            st.markdown("---")

# Display watchlist section
if st.session_state.watchlist:
    st.subheader("📽 Your Movie Night Watchlist:")
    for movie in st.session_state.watchlist:
        with st.container():
            st.markdown(f"### {movie['title']}")
            cols = st.columns([1,3])
            with cols[0]:
                if movie['poster_url']:
                    st.image(movie['poster_url'], width=120)
            with cols[1]:
                if movie['overview']:
                    st.write(movie['overview'])
                st.write(f"**Genres:** {movie['genres']}")
                st.write(f"**Rating:** ⭐ {movie['vote_average']}/10")
            st.markdown("---")