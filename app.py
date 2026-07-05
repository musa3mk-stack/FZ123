import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fz_fassara_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dauko Google Client ID
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '785114901229-n6o1vbp13pq5i1150s76j3ech421rutl.apps.googleusercontent.com')
REDIRECT_URI = "https://fz123.onrender.com/login/google/callback"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='scrypt')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
            
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login/google')
def login_google():
    google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    request_uri = f"{authorization_endpoint}?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile"
    return redirect(request_uri)

@app.route('/login/google/callback')
def google_callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    token_response = requests.post(
        token_endpoint,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": "BA_BU_BU_QATAR_SECRET",
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    )
    
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    userinfo_response = requests.get(userinfo_endpoint, headers=headers)
    
    if userinfo_response.json().get("email_verified"):
        email = userinfo_response.json()["email"]
        username = userinfo_response.json()["name"]
        
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(username=username, email=email, password=None)
            db.session.add(user)
            db.session.commit()
            
        login_user(user)
        return redirect(url_for('dashboard'))
    
    flash("Google authentication failed.")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
