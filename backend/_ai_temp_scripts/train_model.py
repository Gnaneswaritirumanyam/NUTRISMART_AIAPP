import os
import sys
import pandas as pd
import json
import argparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib

def load_data(sample=False):
    print("Loading data...")
    # Paths
    base_dir = r"c:\Users\tirum\OneDrive\Desktop\myapp"
    recipes_csv_path = os.path.join(base_dir, r"backend\archive (8)\recipes.csv")
    reviews_csv_path = os.path.join(base_dir, r"backend\archive (8)\reviews.csv")
    final_data_json_path = os.path.join(base_dir, r"frontend\final_data_updated.recipes.json")
    
    nrows = 10000 if sample else None
    print(f"Loading recipes (sample={sample})...")
    df_recipes = pd.read_csv(recipes_csv_path, nrows=nrows)
    
    print(f"Loading JSON recipes...")
    with open(final_data_json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    if sample:
        json_data = json_data[:2000]
        
    df_json = pd.DataFrame(json_data)
    
    print("Loading reviews...")
    try:
        df_reviews = pd.read_csv(reviews_csv_path, nrows=nrows)
    except Exception as e:
        print("Warning: Could not load reviews.csv", e)
        df_reviews = pd.DataFrame()
        
    return df_recipes, df_json, df_reviews

def train_content_model(df_recipes, df_json):
    print("Training Content-Based Model (TF-IDF)...")
    # Standardize and prepare a corpus
    # 1. From CSV
    csv_texts = []
    csv_ids = []
    for _, row in df_recipes.iterrows():
        name = str(row.get('Name', ''))
        cat = str(row.get('RecipeCategory', ''))
        keys = str(row.get('Keywords', ''))
        text = f"{name} {cat} {keys}".replace('c(', '').replace(')', '').replace('"', '')
        csv_texts.append(text.lower())
        csv_ids.append(str(row.get('RecipeId')))
    # 2. From JSON
    json_texts = []
    json_ids = []
    for _, row in df_json.iterrows():
        name = str(row.get('TranslatedRecipeName', ''))
        cuisine = str(row.get('Cuisine', ''))
        diet = str(row.get('Diet', ''))
        ingreds = " ".join(row.get('main_ingredients', []))
        text = f"{name} {cuisine} {diet} {ingreds}"
        json_texts.append(text.lower())
        json_ids.append(str(row.get('_id', name)))
        
    corpus = csv_texts + json_texts
    item_ids = csv_ids + json_ids
    
    print(f"Total items for content model: {len(corpus)}")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Train nearest neighbors
    nn = NearestNeighbors(n_neighbors=10, metric='cosine')
    nn.fit(tfidf_matrix)
    
    print("Saving content model...")
    os.makedirs(r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\models", exist_ok=True)
    joblib.dump({
        'vectorizer': vectorizer,
        'model': nn,
        'item_ids': item_ids,
        'corpus': corpus
    }, r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\models\content_model.pkl")
    print("Content model saved!")
    
def train_collaborative_model(df_reviews):
    print("Training Collaborative Filtering Model (SVD)...")
    if df_reviews.empty:
        print("No reviews data, skipping.")
        return
        
    try:
        from surprise import Dataset, Reader, SVD
        import surprise
    except ImportError:
        print("scikit-surprise not installed. Skipping CF model.")
        return
        
    # We need AuthorId, RecipeId, Rating
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df_reviews[['AuthorId', 'RecipeId', 'Rating']], reader)
    
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=50, random_state=42)
    print("Fitting SVD...")
    algo.fit(trainset)
    
    print("Saving collaborative model...")
    os.makedirs(r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\models", exist_ok=True)
    joblib.dump(algo, r"c:\Users\tirum\OneDrive\Desktop\myapp\backend\models\collaborative_model.pkl")
    print("Collaborative model saved!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Run on a small sample for testing")
    args = parser.parse_args()
    
    df_rec, df_j, df_rev = load_data(sample=args.sample)
    train_content_model(df_rec, df_j)
    train_collaborative_model(df_rev)
    
    print("AI Training Completed Successfully!")
