import os, joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier

def rebuild_model_if_missing(model_path, seed_csv='data/seed_dataset.csv'):
    if os.path.exists(model_path):
        return
    # train quick model on seed CSV included in the project
    if not os.path.exists(seed_csv):
        raise FileNotFoundError('Seed dataset not found for model rebuild.')
    df = pd.read_csv(seed_csv)
    features = [c for c in df.columns if c != 'label']
    X = df[features].values
    y = df['label'].values
    clf = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
    clf.fit(X,y)
    joblib.dump({'model': clf, 'features': features}, model_path)
    print('Rebuilt model and saved to', model_path)
