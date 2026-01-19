from utils import create_movies_csv

if __name__ == "__main__":
    print("Creating movies database...")
    df = create_movies_csv()
    if df is not None:
        print(f"Database created with {len(df)} movies.")
    else:
        print("Failed to create database.")