from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import joblib, os, csv
import numpy as np
from datetime import datetime
from rebuild_model import rebuild_model_if_missing

app = Flask(__name__)
app.secret_key = 'dev-secret-key-ctauth'

MODEL_PATH = 'model.joblib'
DATASET_PATH = 'data/personal_behavior.csv'

# ensure model exists (train locally if missing)
rebuild_model_if_missing(MODEL_PATH, seed_csv='data/seed_dataset.csv')

artefact = joblib.load(MODEL_PATH)
model = artefact['model']
FEATURES = artefact['features']

# per-session suspicious counters
session_counters = {}
PROB_THRESHOLD = 0.40
REQUIRED_CONSECUTIVE = 3

def log_sample(feature_dict, label='normal'):
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    file_exists = os.path.isfile(DATASET_PATH)
    with open(DATASET_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(list(feature_dict.keys()) + ['label','timestamp'])
        writer.writerow(list(feature_dict.values()) + [label, datetime.now().isoformat()])

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('shop'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username','')
        password = request.form.get('password','')
        # demo creds
        if username == 'user' and password == 'pass':
            session['user'] = username
            sid = session.get('_id') or str(datetime.now().timestamp())
            session['sid'] = sid
            session_counters[sid] = 0
            return redirect(url_for('shop'))
        else:
            error = 'Invalid credentials. Use user / pass'
    return render_template('login.html', error=error)

@app.route('/shop')
def shop():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('shop.html', user=session.get('user'))

def parse_features(payload):
    try:
        arr = [float(payload.get(f,0)) for f in FEATURES]
        return np.array(arr).reshape(1,-1)
    except:
        return None

@app.route('/track', methods=['POST'])
def track():
    if 'user' not in session:
        return jsonify({'action':'logout','reason':'no_session'})
    sid = session.get('sid')
    data = request.get_json() or {}
    features = data.get('features', {})
    # Log raw sample to personal dataset (label unknown -> 'normal' here)
    try:
        log_sample(features, label='normal')
    except Exception as e:
        app.logger.warning('failed to log sample: %s', e)
    X = parse_features(features)
    if X is None:
        return jsonify({'action':'ok','message':'bad_payload'})
    prob = float(model.predict_proba(X)[0][1])
    suspicious = prob < PROB_THRESHOLD
    # update counter
    session_counters[sid] = int(session_counters.get(sid,0)) + (1 if suspicious else 0)
    if not suspicious:
        session_counters[sid] = 0
    # enforce logout after REQUIRED_CONSECUTIVE suspicious windows
    if session_counters.get(sid,0) >= REQUIRED_CONSECUTIVE:
        # cleanup and instruct frontend to logout
        session_counters.pop(sid, None)
        session.pop('user', None)
        session.pop('sid', None)
        return jsonify({'action':'logout','reason':'anomaly_detected'})
    return jsonify({'action':'ok','prob': round(prob,4), 'suspicious': bool(suspicious), 'count': int(session_counters.get(sid,0))})

@app.route('/logout')
def logout():
    sid = session.pop('sid', None)
    session.pop('user', None)
    session_counters.pop(sid, None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
