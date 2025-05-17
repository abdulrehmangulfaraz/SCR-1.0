import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, app
from models import User
from utils import encrypt_data

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('scan.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html')
        
        login_user(user, remember=True)
        logger.info(f"User {username} logged in successfully")
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.is_admin:
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('scan.dashboard')
        
        return redirect(next_page)
    
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('scan.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            flash('Please fill all required fields', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user with encrypted data
        encrypted_email = encrypt_data(email)
        encrypted_username = encrypt_data(username)
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            encrypted_email=encrypted_email,
            encrypted_username=encrypted_username
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"New user registered: {username}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    from models import ScanHistory
    from datetime import datetime, timedelta
    
    # Get user's scan statistics
    total_scans = ScanHistory.query.filter_by(user_id=current_user.id).count()
    
    # Get scans from this month
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = ScanHistory.query.filter_by(user_id=current_user.id).filter(ScanHistory.scan_date >= first_day_of_month).count()
    
    # Get high risk and safe scans
    high_risk_scans = ScanHistory.query.filter_by(user_id=current_user.id, risk_level='High Risk').count()
    safe_scans = ScanHistory.query.filter_by(user_id=current_user.id, risk_level='Low Risk').count()
    
    # Get recent activity (last 5 scans)
    recent_scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scan_date.desc()).limit(5).all()
    
    recent_activities = []
    for scan in recent_scans:
        time_diff = datetime.utcnow() - scan.scan_date
        
        if time_diff < timedelta(minutes=1):
            time_str = "Just now"
        elif time_diff < timedelta(hours=1):
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        elif time_diff < timedelta(days=1):
            hours = time_diff.seconds // 3600
            time_str = f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif time_diff < timedelta(days=30):
            days = time_diff.days
            time_str = f"{days} {'day' if days == 1 else 'days'} ago"
        else:
            time_str = scan.scan_date.strftime('%Y-%m-%d')
            
        recent_activities.append({
            'time': time_str,
            'action': f"Scanned {scan.domain}",
            'icon': 'fas fa-search',
            'color': 'info'
        })
    
    # Add login activity (if it's recent)
    login_time_diff = datetime.utcnow() - current_user.created_at
    if login_time_diff < timedelta(days=30):
        days = login_time_diff.days
        if days < 1:
            hours = login_time_diff.seconds // 3600
            if hours < 1:
                minutes = login_time_diff.seconds // 60
                time_str = f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
            else:
                time_str = f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        else:
            time_str = f"{days} {'day' if days == 1 else 'days'} ago"
        
        recent_activities.append({
            'time': time_str,
            'action': 'Account created',
            'icon': 'fas fa-user-plus',
            'color': 'primary'
        })
    
    stats = {
        'total_scans': total_scans,
        'scans_this_month': scans_this_month,
        'high_risk_scans': high_risk_scans,
        'safe_scans': safe_scans
    }
    
    return render_template('profile.html', stats=stats, activities=recent_activities)

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('Please fill all required fields', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.profile'))
    
    current_user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        flash('Password updated successfully', 'success')
        logger.info(f"User {current_user.username} changed password")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating password: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
    
    return redirect(url_for('auth.profile'))
