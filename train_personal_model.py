import pandas as pd, joblib, os
from sklearn.ensemble import RandomForestClassifier
DATA = 'data/personal_behavior.csv'
OUT = 'model_personal.joblib'
if not os.path.exists(DATA):
    print('No personal data file found. Interact with site to collect samples first.')
    exit()
df = pd.read_csv(DATA)
df = df.drop(columns=['label','timestamp'], errors='ignore')
X = df.values
# create pseudo labels: assume all collected are normal -> create 'normal' class as 1 and generate negatives by small perturbation
y = [1]*len(X)
# augment negatives by adding noise to make class 0
import numpy as np
X_neg = X * (1 + 0.5 * np.random.randn(*X.shape))
X_all = np.vstack([X, X_neg])
y_all = y + [0]*len(X_neg)
clf = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
clf.fit(X_all, y_all)
joblib.dump({'model': clf, 'features': list(df.columns)}, OUT)
print('Trained personal model ->', OUT)
