# RetailAI — AI Based Supply & Demand Prediction System
## Final Year Project

---

## 📁 Folder Structure
```
project/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── templates/              # HTML templates
│   ├── base.html           # Base layout with navbar/footer
│   ├── home.html           # Landing page
│   ├── signup.html         # Registration with OTP
│   ├── login.html          # Login page
│   ├── dashboard.html      # Main app (upload, predict, charts)
│   ├── pricing.html        # Plans (Free / Monthly / Yearly)
│   ├── receipt.html        # Payment receipt
│   ├── about.html          # About the project
│   └── contact.html        # Contact form
├── static/
│   ├── css/main.css        # All styles
│   └── js/main.js          # Shared JavaScript
├── database/               # SQLite database (auto-created)
├── uploads/                # Uploaded CSV files (auto-created)
└── dataset/
    └── sample_retail_data.csv  # Sample dataset for testing
```

---

## ⚡ Setup (VS Code)

### 1. Install Python 3.11+
Download from https://python.org

### 2. Create virtual environment
```bash
cd project
python -m venv venv
```
Activate:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Email (for OTP)
Open `app.py` and update lines 17-18:
```python
app.config['MAIL_USERNAME'] = 'your_gmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_16_char_app_password'
```
> For Gmail: Enable 2FA → Search "App Passwords" → Create one for "Mail"

**⚠️ If you skip email config, OTP won't be sent but the route still works.**
> For testing without email: manually set `is_verified=1` in the DB.

### 5. Run the app
```bash
python app.py
```

Open browser: **http://127.0.0.1:5000**

---

## 🧪 Testing Without Email
1. Run app, go to /signup, fill form → it'll show OTP box
2. Open SQLite DB (use DB Browser for SQLite)
3. Open `database/retail.db` → `users` table
4. Set `is_verified = 1` for your user
5. Now login works!

---

## 📊 Sample Dataset
Use `dataset/sample_retail_data.csv` for testing.
- Products: Rice, Wheat Flour, Sugar, Mobile Phone, T-Shirt
- Columns: product_name, category, month, price, units_sold, promotions, season, demand
- Select `product_name` as product column
- Select `demand` or `units_sold` as sales column

---

## 💳 Payment Plans (Simulated)
- Free: 3 predictions
- Monthly Pro: ₹499/month — unlimited predictions
- Yearly Pro: ₹3,999/year — unlimited + all features
> No real payment gateway. Academic project only.

---

## 🔑 Features
- ✅ Email OTP verification
- ✅ SHA-256 password hashing
- ✅ CSV upload & preview
- ✅ Linear Regression + Random Forest ML
- ✅ Interactive Chart.js charts
- ✅ Inventory recommendations
- ✅ Prediction history
- ✅ Pricing plans in INR
- ✅ Printable receipts
- ✅ Toast notifications
- ✅ Mobile responsive
- ✅ Glassmorphism dark UI
