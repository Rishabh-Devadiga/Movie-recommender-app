# Movie Recommendation App

A Streamlit-based movie recommendation application that suggests similar movies based on the current 100 popular movies with content-based filtering. The algorithm I made uses TF-IDF and cosine similarity to suggest similar movies. The app uses TMDB API for movie data and stores it in a csv file. It provides a user-friendly interface for discovering new movies.

## Features

- Content-based movie recommendations
- Movie search functionality
- Watchlist management
- Dark/Light mode toggle
- Responsive UI with movie posters and details

## Prerequisites

- Python 3.7+
- Streamlit
- Pandas
- scikit-learn
- requests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/movie-recommendation-app.git
cd movie-recommendation-app
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Get your TMDB API key from [TMDB](https://www.themoviedb.org/documentation/api) and replace the API_KEY in the code.

## Usage

Run the Streamlit app:
```bash
streamlit run movie_app.py
```

## How it Works

The app uses content-based filtering to recommend movies based on:
- Movie overviews
- Genres
- Similarity scores calculated using TF-IDF and cosine similarity

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
