import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# High-performance enterprise system directory mapping
project_root = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(project_root, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fz_fassara_mega_ultra_premium_key_2026')

# ENVIRONMENT-ADAPTIVE DATABASE CONFIGURATION MATRIX (SQLite for Local Pydroid3, PostgreSQL for Render)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    db_path = os.path.join(project_root, 'vtu_database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth2 Credentials Configurations (Fetches dynamically from Render Environment Variables)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Maximum 200MB file processing safety threshold
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
app.config['UPLOAD_VIDEO_DIR'] = os.path.join(project_root, 'uploads')
app.config['UPLOAD_THUMB_DIR'] = os.path.join(project_root, 'thumbnails')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Automatic offline media storage setup folders
for folder in [app.config['UPLOAD_VIDEO_DIR'], app.config['UPLOAD_THUMB_DIR']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# HARDCODED SUPER ADMIN CREDENTIALS CONFIGURATION
ADMIN_EMAIL = "musa3mk@gmail.com"
ADMIN_PASSWORD_PLAIN = "FZ12345@"

# =========================================================================
# ADVANCED ENTERPRISE DATABASE SCHEMA MATRIX (100% EXPANDED CAPABILITY)
# =========================================================================

subscribers = db.Table('subscribers',
    db.Column('channel_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('subscriber_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=True) # Modified to Nullable for direct Google Logins
    bio = db.Column(db.String(300), default='No bio available.')
    profile_pic = db.Column(db.String(200), default='default_avatar.png')
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    videos = db.relationship('Video', backref='uploader', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    history = db.relationship('WatchHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    watchlist = db.relationship('WatchLater', backref='user', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('VideoLike', backref='user', lazy=True, cascade="all, delete-orphan")

    subscriptions = db.relationship(
        'User', secondary=subscribers,
        primaryjoin=(subscribers.c.subscriber_id == id),
        secondaryjoin=(subscribers.c.channel_id == id),
        backref=db.backref('channel_subscribers', lazy='dynamic'),
        lazy='dynamic'
    )

class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False) 
    filename = db.Column(db.String(200), nullable=False)
    thumbnail = db.Column(db.String(200), nullable=False)
    is_locked = db.Column(db.Boolean, default=False) 
    is_short = db.Column(db.Boolean, default=False) 
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('Comment', backref='video', lazy=True, cascade="all, delete-orphan")
    history_entries = db.relationship('WatchHistory', backref='video', lazy=True, cascade="all, delete-orphan")
    watchlist_entries = db.relationship('WatchLater', backref='video', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('VideoLike', backref='video', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True) 
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade="all, delete-orphan")

class WatchHistory(db.Model):
    __tablename__ = 'watch_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)

class WatchLater(db.Model):
    __tablename__ = 'watch_later'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class VideoLike(db.Model):
    __tablename__ = 'video_likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Injection script for automated browser notification client runtime prompts
@app.context_processor
def inject_permissions_script():
    script = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        if ("Notification" in window) {
            if (Notification.permission !== "granted" && Notification.permission !== "denied") {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        console.log("Notification access authorized successfully.");
                    }
                });
            }
        }
    });
    </script>
    """
    return dict(notification_prompt_script=script)

# =========================================================================
# CORE CONTROLLER OPERATIONS ENGINE
# =========================================================================

@app.route('/')
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('welcome.html')

# DYNAMIC GOOGLE LOGIN REROUTING SYSTEM
@app.route('/login/google')
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google Auth parameters are missing in configurations.", "danger")
        return redirect(url_for('welcome'))
        
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    redirect_uri = request.host_url.rstrip('/') + url_for('google_callback')
    
    request_uri = requests.Request(
        "GET",
        authorization_endpoint,
        params={
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
        },
    ).prepare().url
    return redirect(request_uri)

@app.route('/login/google/callback')
def google_callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    redirect_uri = request.host_url.rstrip('/') + url_for('google_callback')

    token_response = requests.post(
        token_endpoint,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )

    token_backend_data = token_response.json()
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = requests.Request(
        "GET", userinfo_endpoint, headers={"Authorization": f"Bearer {token_backend_data['access_token']}"}
    ).prepare().url, {"Authorization": f"Bearer {token_backend_data['access_token']}"}, None
    
    userinfo_response = requests.get(uri, headers=headers)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"].strip().lower()
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User.query.filter_by(email=users_email).first()
    if not user:
        user = User(name=users_name, email=users_email, is_admin=False)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(name=name, email=email, password_hash=hashed_password, is_admin=False)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email or password.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    query = Video.query.filter_by(is_short=False)
    
    if search_query:
        query = query.join(User).filter(
            (Video.title.like(f"%{search_query}%")) | 
            (User.name.like(f"%{search_query}%"))
        )
    if category_filter:
        query = query.filter(Video.category == category_filter)
        
    all_videos = query.order_by(Video.id.desc()).all()
    return render_template('dashboard.html', user=current_user, name=current_user.name, videos=all_videos, active_tab='home')

@app.route('/shorts')
@login_required
def shorts_tv():
    short_videos = Video.query.filter_by(is_short=True).order_by(Video.id.desc()).all()
    return render_template('dashboard.html', user=current_user, name=current_user.name, videos=short_videos, active_tab='shorts')

@app.route('/premium_hub')
@login_required
def premium_hub():
    premium_videos = Video.query.filter_by(is_locked=True).order_by(Video.id.desc()).all()
    return render_template('dashboard.html', user=current_user, name=current_user.name, videos=premium_videos, active_tab='premium')

@app.route('/my_downloads')
@login_required
def my_downloads():
    downloaded_records = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.id.desc()).limit(10).all()
    return render_template('dashboard.html', user=current_user, name=current_user.name, records=downloaded_records, active_tab='downloads')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_bio = request.form.get('bio')
        avatar_file = request.files.get('avatar_file')
        
        if new_name:
            current_user.name = new_name
        if new_bio:
            current_user.bio = new_bio
            
        if avatar_file and avatar_file.filename != '':
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join(app.config['UPLOAD_THUMB_DIR'], avatar_filename))
            current_user.profile_pic = avatar_filename
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile'))
        
    return render_template('dashboard.html', user=current_user, name=current_user.name, active_tab='me')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/stream/video/<filename>')
@login_required
def stream_video(filename):
    return send_from_directory(app.config['UPLOAD_VIDEO_DIR'], filename)

@app.route('/stream/thumb/<filename>')
def stream_thumb(filename):
    return send_from_directory(app.config['UPLOAD_THUMB_DIR'], filename)

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
@login_required
def watch_video(video_id):
    video = Video.query.get_or_404(video_id)
    
    if video.is_locked and not current_user.is_premium and not current_user.is_admin:
        flash('This is a Premium Video. You need to unlock premium tier access first.', 'warning')
        return redirect(url_for('premium_hub'))
        
    video.views += 1
    history_entry = WatchHistory(user_id=current_user.id, video_id=video.id)
    db.session.add(history_entry)
    db.session.commit()
    
    recommended = Video.query.filter(Video.category == video.category, Video.id != video.id).limit(4).all()
    
    if request.method == 'POST' and 'comment_text' in request.form:
        comment_text = request.form.get('comment_text')
        parent_id = request.form.get('parent_id')
        
        if comment_text:
            new_comment = Comment(
                video_id=video.id, user_id=current_user.id, 
                text=comment_text, parent_id=int(parent_id) if parent_id else None
            )
            db.session.add(new_comment)
            
            if parent_id:
                parent_comment = Comment.query.get(int(parent_id))
                if parent_comment and parent_comment.user_id != current_user.id:
                    notif = Notification(user_id=parent_comment.user_id, message=f"{current_user.name} replied to your comment on movie: {video.title}")
                    db.session.add(notif)
                    
            db.session.commit()
            flash('Comment added!', 'success')
            return redirect(url_for('watch_video', video_id=video.id))

    likes_count = VideoLike.query.filter_by(video_id=video.id).count()
    has_liked = VideoLike.query.filter_by(user_id=current_user.id, video_id=video.id).first() is not None
    
    return render_template('video.html', video=video, likes=likes_count, has_liked=has_liked, recommended=recommended)

@app.route('/video/<int:video_id>/like')
@login_required
def like_video(video_id):
    video = Video.query.get_or_404(video_id)
    existing_like = VideoLike.query.filter_by(user_id=current_user.id, video_id=video.id).first()
    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = VideoLike(user_id=current_user.id, video_id=video.id)
        db.session.add(new_like)
    db.session.commit()
    return redirect(url_for('watch_video', video_id=video.id))

@app.route('/watchlist')
@login_required
def watchlist():
    items = WatchLater.query.filter_by(user_id=current_user.id).order_by(WatchLater.id.desc()).all()
    return render_template('watchlist.html', items=items)

@app.route('/video/<int:video_id>/watchlist/add')
@login_required
def add_to_watchlist(video_id):
    video = Video.query.get_or_404(video_id)
    exists = WatchLater.query.filter_by(user_id=current_user.id, video_id=video.id).first()
    if not exists:
        entry = WatchLater(user_id=current_user.id, video_id=video.id)
        db.session.add(entry)
        db.session.commit()
        flash('Added to Watch Later!', 'success')
    return redirect(url_for('watch_video', video_id=video.id))

@app.route('/history')
@login_required
def watch_history_page():
    records = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.id.desc()).all()
    return render_template('history.html', records=records)

@app.route('/video/<int:video_id>/download')
@login_required
def download_video(video_id):
    video = Video.query.get_or_404(video_id)
    video.downloads += 1
    db.session.commit()
    return send_from_directory(app.config['UPLOAD_VIDEO_DIR'], video.filename, as_attachment=True)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        is_premium_wall = request.form.get('is_premium') == 'true'
        is_short_tv = request.form.get('is_short') == 'true'
        
        video_file = request.files.get('video_file')
        thumb_file = request.files.get('thumbnail_file')
        
        if video_file and thumb_file:
            video_filename = secure_filename(video_file.filename)
            thumb_filename = secure_filename(thumb_file.filename)
            
            video_file.save(os.path.join(app.config['UPLOAD_VIDEO_DIR'], video_filename))
            thumb_file.save(os.path.join(app.config['UPLOAD_THUMB_DIR'], thumb_filename))
            
            new_video = Video(
                user_id=current_user.id, title=title, description=description,
                category=category, filename=video_filename, thumbnail=thumb_filename,
                is_locked=is_premium_wall, is_short=is_short_tv
            )
            db.session.add(new_video)
            db.session.commit()
            flash('Video published successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    all_users = User.query.all()
    all_videos = Video.query.all()
    return render_template('admin.html', users=all_users, videos=all_videos)

@app.route('/admin/delete/video/<int:video_id>')
@login_required
def admin_delete_video(video_id):
    if not current_user.is_admin:
        abort(403)
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    flash('Video deleted permanently.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin account!', 'danger')
        return redirect(url_for('admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted permanently.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('welcome'))

def init_super_admin():
    admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin_user:
        hashed_pw = generate_password_hash(ADMIN_PASSWORD_PLAIN, method='scrypt')
        super_admin = User(
            name="Super Admin",
            email=ADMIN_EMAIL,
            password_hash=hashed_pw,
            is_admin=True,
            is_premium=True,
            bio="Main System Control Administration Account Platform"
        )
        db.session.add(super_admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_super_admin()
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
