from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, hashlib, random, string, json, re
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import uuid

app = Flask(__name__)
app.secret_key = 'supplydemand_ai_secret_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect('database/retail.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs('database', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('dataset', exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            otp TEXT,
            otp_expiry TEXT,
            plan TEXT DEFAULT 'free',
            plan_expiry TEXT,
            free_predictions INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            predicted_demand REAL,
            confidence REAL,
            model_used TEXT,
            file_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            original_name TEXT,
            rows INTEGER,
            columns INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_id TEXT UNIQUE,
            plan TEXT,
            amount REAL,
            currency TEXT DEFAULT 'INR',
            status TEXT DEFAULT 'pending',
            receipt_number TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

# ---------- HELPERS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def get_user(email):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return user

def can_predict(user):
    if user['plan'] in ('monthly','yearly'):
        expiry = user['plan_expiry']
        if expiry and datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S') > datetime.now():
            return True, 'paid'
    if user['free_predictions'] > 0:
        return True, 'free'
    return False, 'limit'

# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        message = request.form.get('message','').strip()
        if not name or not email or not message:
            return jsonify({'success': False, 'message': 'Please fill in all contact fields.'})
        conn = get_db()
        conn.execute('INSERT INTO contacts (name,email,message) VALUES (?,?,?)',
                     (name, email, message))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message sent successfully!'});
    return render_template('contact.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']
        if len(phone) < 10:
            return jsonify({'success': False, 'message': 'Phone number must be at least 10 digits!'})
        if password != confirm:
            return jsonify({'success': False, 'message': 'Passwords do not match!'})
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters!'})
        conn = get_db()
        existing = conn.execute('SELECT id FROM users WHERE email=? OR phone=?', (email, phone)).fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Email or phone already registered!'})
        otp = generate_otp()
        expiry = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        hashed = hash_password(password)
        conn.execute('INSERT INTO users (username,email,phone,password,otp,otp_expiry) VALUES (?,?,?,?,?,?)',
                     (username, email, phone, hashed, otp, expiry))
        conn.commit()
        conn.close()
        print(f"🔸 Simulated SMS to {phone}: {otp}")
        print("💬 Enter the OTP in the app to verify.")
        return jsonify({'success': True, 'message': 'OTP sent to your phone! Check console or enter below.', 'phone': phone, 'otp': otp})
    return render_template('signup.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    phone = data.get('phone','').strip()
    otp_entered = data.get('otp','').strip()
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE phone=?', (phone,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found!'})
    if user['otp'] != otp_entered:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid OTP!'})
    if datetime.strptime(user['otp_expiry'], '%Y-%m-%d %H:%M:%S') < datetime.now():
        conn.close()
        return jsonify({'success': False, 'message': 'OTP expired! Please signup again.'})
    conn.execute('UPDATE users SET is_verified=1, otp=NULL, otp_expiry=NULL WHERE phone=?', (phone,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Phone verified! You can now login.'})

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = get_user(email)
        if not user:
            return jsonify({'success': False, 'message': 'Email not registered!'})
        if not user['is_verified']:
            return jsonify({'success': False, 'message': 'Please verify your phone first!'})
        if user['password'] != hash_password(password):
            return jsonify({'success': False, 'message': 'Wrong password!'})
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session['phone'] = user['phone']
        return jsonify({'success': True, 'message': f'Welcome back, {user["username"]}!', 'redirect': '/dashboard'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    conn = get_db()
    predictions = conn.execute(
        'SELECT * FROM predictions WHERE user_id=? ORDER BY created_at DESC LIMIT 10',
        (session['user_id'],)).fetchall()
    files = conn.execute(
        'SELECT * FROM uploaded_files WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 5',
        (session['user_id'],)).fetchall()
    total_preds = conn.execute(
        'SELECT COUNT(*) as cnt FROM predictions WHERE user_id=?',
        (session['user_id'],)).fetchone()['cnt']
    conn.close()
    can_pred, pred_type = can_predict(user)
    return render_template('dashboard.html', user=user, predictions=predictions,
                           files=files, total_preds=total_preds,
                           can_predict=can_pred, pred_type=pred_type)

# ... rest of the code remains the same
@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in!'})
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected!'})
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Please upload a valid CSV file!'})
    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)
    try:
        df = pd.read_csv(filepath)
        rows, cols = df.shape
        conn = get_db()
        conn.execute('INSERT INTO uploaded_files (user_id,filename,original_name,rows,columns) VALUES (?,?,?,?,?)',
                     (session['user_id'], unique_name, original_name, rows, cols))
        conn.commit()
        conn.close()
        columns = df.columns.tolist()
        preview = df.head(10).to_dict('records')
        # Guess product column
        product_col = None
        for c in df.columns:
            if c.lower() in ['product','product_name','item','item_name','name','sku']:
                product_col = c
                break
        products = df[product_col].unique().tolist() if product_col else []
        session['current_file'] = unique_name
        session['product_col'] = product_col
        return jsonify({'success': True, 'message': f'File uploaded! {rows} rows, {cols} columns.',
                        'columns': columns, 'preview': preview, 'products': products,
                        'product_col': product_col, 'rows': rows, 'cols': cols})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error reading CSV: {str(e)}'})


def _load_user_csv():
    file_name = session.get('current_file')
    if not file_name:
        return None, 'No file uploaded for prediction.'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    if not os.path.exists(filepath):
        return None, 'Uploaded file not found.'
    try:
        df = pd.read_csv(filepath)
        return df, None
    except Exception as e:
        return None, f'Error loading uploaded file: {e}'


def _detect_sales_column(df):
    candidates = ['sales', 'demand', 'quantity', 'units', 'sold', 'sales_count']
    for col in df.columns:
        if col.lower() in candidates:
            return col
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    return numeric_cols[0] if numeric_cols else None


@app.route('/get-products', methods=['POST'])
def get_products():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in!'})
    data = request.get_json(silent=True) or {}
    product_col = data.get('product_col') or session.get('product_col')
    if not product_col:
        return jsonify({'success': False, 'message': 'Product column not selected!'})
    df, err = _load_user_csv()
    if err:
        return jsonify({'success': False, 'message': err})
    if product_col not in df.columns:
        return jsonify({'success': False, 'message': f'Product column "{product_col}" not found in file.'})
    values = df[product_col].dropna().unique().tolist()
    values = sorted([str(v) for v in values if str(v).strip() != ''])
    return jsonify({'success': True, 'products': values[:200]})


@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in!'})
    user = get_user_by_id(session['user_id'])
    can_pred, pred_type = can_predict(user)
    if not can_pred:
        return jsonify({'success': False, 'message': 'limit'})
    data = request.get_json(silent=True) or {}
    product_col = data.get('product_col') or session.get('product_col')
    sales_col = data.get('sales_col')
    product = data.get('product')
    model_type = data.get('model_type', 'random_forest')
    if not product_col:
        return jsonify({'success': False, 'message': 'Product column not selected!'})
    df, err = _load_user_csv()
    if err:
        return jsonify({'success': False, 'message': err})
    if product_col not in df.columns:
        return jsonify({'success': False, 'message': f'Product column "{product_col}" not found in file.'})
    if product:
        df = df[df[product_col].astype(str) == str(product)]
    if df.empty:
        return jsonify({'success': False, 'message': 'No rows match the selected product.'})
    if not sales_col:
        sales_col = _detect_sales_column(df)
    if not sales_col or sales_col not in df.columns:
        return jsonify({'success': False, 'message': 'Sales/Demand column not found. Please select it manually.'})
    y = pd.to_numeric(df[sales_col], errors='coerce').dropna()
    if y.empty:
        return jsonify({'success': False, 'message': f'Sales/Demand column "{sales_col}" contains no numeric values.'})
    df = df.loc[y.index]
    date_col = None
    for col in df.columns:
        if col.lower() in ['date', 'timestamp', 'time', 'day']:
            date_col = col
            break
    if date_col:
        labels = df[date_col].astype(str).tolist()
    else:
        labels = [str(i + 1) for i in range(len(df))]
    X = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression() if model_type == 'linear' else RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y.values)
    y_pred = model.predict(X)
    next_pred = float(model.predict(np.array([[len(y)]]))[0])
    predicted_demand = round(max(0.0, next_pred), 2)
    predicted = [round(float(v), 2) for v in y_pred]
    historical = [round(float(v), 2) for v in y.values]
    mean_demand = round(float(np.mean(y)), 2)
    r2 = round(float(r2_score(y, y_pred)) * 100, 2)
    mae = round(float(mean_absolute_error(y, y_pred)), 2)
    if predicted_demand >= mean_demand * 1.2:
        rec = {'level': 'high', 'color': 'green', 'icon': '🔥', 'text': 'Demand looks strong. Stock up to avoid shortages.'}
    elif predicted_demand <= mean_demand * 0.8:
        rec = {'level': 'low', 'color': 'red', 'icon': '📉', 'text': 'Demand seems light. Consider a smaller reorder.'}
    else:
        rec = {'level': 'moderate', 'color': 'yellow', 'icon': '⚖️', 'text': 'Demand is stable. Maintain normal stock levels.'}
    conn = get_db()
    conn.execute('INSERT INTO predictions (user_id, product, predicted_demand, confidence, model_used, file_name) VALUES (?,?,?,?,?,?)',
                 (user['id'], product or 'all', predicted_demand, round(r2, 2), model_type, session.get('current_file')))
    if user['plan'] == 'free':
        conn.execute('UPDATE users SET free_predictions = free_predictions - 1 WHERE id=?', (user['id'],))
    conn.commit()
    conn.close()
    if user['plan'] == 'free':
        user = get_user_by_id(user['id'])
        remaining = user['free_predictions']
    else:
        remaining = 'unlimited'
    return jsonify({
        'success': True,
        'message': 'Prediction completed successfully!',
        'predicted_demand': predicted_demand,
        'mean_demand': mean_demand,
        'r2': r2,
        'mae': mae,
        'labels': labels,
        'historical': historical,
        'predicted': predicted,
        'recommendation': rec,
        'remaining_predictions': remaining
    })


@app.route('/api/dashboard-stats')
def dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'labels': [], 'values': []})
    conn = get_db()
    rows = conn.execute('SELECT predicted_demand, created_at FROM predictions WHERE user_id=? ORDER BY created_at DESC LIMIT 8',
                        (session['user_id'],)).fetchall()
    conn.close()
    rows = rows[::-1]
    labels = [row['created_at'][:10] for row in rows]
    values = [row['predicted_demand'] for row in rows]
    return jsonify({'labels': labels, 'values': values})


@app.route('/pricing')
def pricing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    return render_template('pricing.html', user=user)


@app.route('/purchase', methods=['POST'])
def purchase():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in!'})
    data = request.get_json(silent=True) or {}
    plan = data.get('plan')
    card_name = data.get('card_name', '').strip()
    card_number = data.get('card_number', '').replace(' ', '')
    card_expiry = data.get('card_expiry', '').strip()
    card_cvv = data.get('card_cvv', '').strip()
    if plan not in ('monthly', 'yearly'):
        return jsonify({'success': False, 'message': 'Invalid plan selected.'})
    if not card_name or len(card_name) < 3:
        return jsonify({'success': False, 'message': 'Please enter the cardholder name.'})
    if not card_number.isdigit() or len(card_number) not in (15, 16):
        return jsonify({'success': False, 'message': 'Enter a valid card number (15-16 digits).'})
    if not re.match(r'^(0[1-9]|1[0-2])\/[0-9]{2}$', card_expiry):
        return jsonify({'success': False, 'message': 'Enter expiry in MM/YY format.'})
    if not card_cvv.isdigit() or len(card_cvv) not in (3, 4):
        return jsonify({'success': False, 'message': 'Enter a valid 3- or 4-digit CVV.'})
    user = get_user_by_id(session['user_id'])
    if user['plan'] == plan:
        return jsonify({'success': False, 'message': 'You already have this plan active.'})
    amount = 499 if plan == 'monthly' else 3999
    expiry = datetime.now() + timedelta(days=30) if plan == 'monthly' else datetime.now() + timedelta(days=365)
    plan_expiry = expiry.strftime('%Y-%m-%d %H:%M:%S')
    transaction_id = uuid.uuid4().hex
    receipt_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    conn = get_db()
    conn.execute('UPDATE users SET plan=?, plan_expiry=? WHERE id=?', (plan, plan_expiry, user['id']))
    conn.execute('INSERT INTO transactions (user_id, transaction_id, plan, amount, status, receipt_number) VALUES (?,?,?,?,?,?)',
                 (user['id'], transaction_id, plan, amount, 'success', receipt_number))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'{plan.capitalize()} plan activated successfully!', 'transaction_id': transaction_id})


@app.route('/get-receipt/<transaction_id>')
def get_receipt(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    conn = get_db()
    tx = conn.execute('SELECT * FROM transactions WHERE transaction_id=? AND user_id=?',
                      (transaction_id, session['user_id'])).fetchone()
    conn.close()
    if not tx:
        return redirect(url_for('pricing'))
    return render_template('receipt.html', tx=tx, user=user)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
