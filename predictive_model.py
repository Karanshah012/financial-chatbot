# predictive_model.py
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
from pathlib import Path

Path("models").mkdir(parents=True, exist_ok=True)

def train_and_save():
    try:
        df = pd.read_csv("data/user_transactions.csv")
    except FileNotFoundError:
        print("No data/user_transactions.csv found. Create sample data to train predictive model.")
        return
    X = df[["month_index"]]
    y = df["spending"]
    model = LinearRegression()
    model.fit(X, y)
    pickle.dump(model, open("models/predictive_model.pkl", "wb"))
    print("Saved models/predictive_model.pkl")

if __name__ == "__main__":
    train_and_save()
