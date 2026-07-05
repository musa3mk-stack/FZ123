import os
import base64
import json
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
    # Amfani da response_type=id_token domin kaucewa bukatar Client Secret gaba daya
    google_provider_cfg = requests.get("https://accounts.google.com/.well-known/openid-configuration").json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Muna amfani da response_mode=form_post don karban bayanan sirri lafiya
    request_uri = (
        f"{authorization_endpoint}?response_type=id_token&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid%20email%20profile"
        f"&nonce=fz123nonce&response_mode=form_post"
    )
    return redirect(request_uri)

@app.route('/login/google/callback', methods=['POST'])
def google_callback():
    # Google zai turo id_token ta hanyar POST request
    id_token = request.form.get("id_token")
    if not id_token:
        flash("Google authentication failed: Missing token.")
        return redirect(url_for('login'))
    
    try:
        # Fassarar id_token ba tare da bukatar wani library na daban ba
        segments = id_token.split('.')
        if len(segments) < 2:
            raise ValueError("Invalid token")
            
        payload_b64 = segments[1]
        # Gyara padding na base64 idan akwai bukata
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        user_info = json.loads(payload_json)
        
        email = user_info.get("email")
        username = user_info.get("name", email.split('@')[0])
        
        if email:
            user = User.query.filter_by(email=email).first()
            if not user:
                # Idan babu shi, mu kirkiri sabon asusu
                user = User(username=username, email=email, password=None)
                db.session.add(user)
                db.session.commit()
                
            login_user(user)
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        flash(f"Error decoding Google login: {str(e)}")
        
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
