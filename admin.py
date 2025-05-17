import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import User, ScanHistory, BlockedDomain, ScanStatistics, AdminUser

bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)

@bp.before_request
def check_admin():
    """Check if user is an admin before processing any admin route"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.url))
    
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('scan.dashboard'))

@bp.route('/')
@login_required
def dashboard():
    # Get platform statistics
    stats = {
        'total_users': User.query.count(),
        'total_scans': ScanHistory.query.count(),
        'blocked_domains': BlockedDomain.query.count(),
        'scans_today': ScanHistory.query.filter(
            ScanHistory.scan_date >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
    }
    
    # Get most scanned domains
    most_scanned = ScanStatistics.query.order_by(ScanStatistics.scan_count.desc()).limit(10).all()
    
    # Get recent scans
    recent_scans = ScanHistory.query.order_by(ScanHistory.scan_date.desc()).limit(10).all()
    
    # Get risk distribution
    risk_distribution = {
        'high': ScanHistory.query.filter_by(risk_level='High Risk').count(),
        'medium': ScanHistory.query.filter_by(risk_level='Medium Risk').count(),
        'low': ScanHistory.query.filter_by(risk_level='Low Risk').count()
    }
    
    # Get active users (users with scans in the last 7 days)
    active_users_count = db.session.query(User).join(ScanHistory).filter(
        ScanHistory.scan_date >= datetime.utcnow() - timedelta(days=7)
    ).distinct().count()
    
    stats['active_users'] = active_users_count
    
    return render_template('admin_dashboard.html', 
                           stats=stats, 
                           most_scanned=most_scanned, 
                           recent_scans=recent_scans,
                           risk_distribution=risk_distribution)

@bp.route('/users')
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/users.html', users=users)

@bp.route('/domains')
@login_required
def domains():
    page = request.args.get('page', 1, type=int)
    domains = ScanStatistics.query.order_by(ScanStatistics.scan_count.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    blocked = BlockedDomain.query.all()
    blocked_domains = [d.domain for d in blocked]
    
    return render_template('admin/domains.html', domains=domains, blocked_domains=blocked_domains)

@bp.route('/block_domain', methods=['POST'])
@login_required
def block_domain():
    domain = request.form.get('domain')
    reason = request.form.get('reason')
    
    if not domain:
        flash('Domain name is required', 'danger')
        return redirect(url_for('admin.domains'))
    
    # Check if domain is already blocked
    existing = BlockedDomain.query.filter_by(domain=domain).first()
    if existing:
        flash(f'Domain {domain} is already blocked', 'warning')
        return redirect(url_for('admin.domains'))
    
    # Create new blocked domain
    blocked = BlockedDomain(
        domain=domain,
        reason=reason,
        blocked_by=current_user.id,
        blocked_at=datetime.utcnow()
    )
    
    try:
        db.session.add(blocked)
        db.session.commit()
        flash(f'Domain {domain} has been blocked', 'success')
        logger.info(f"Admin {current_user.username} blocked domain {domain}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error blocking domain: {str(e)}")
        flash('An error occurred while blocking the domain', 'danger')
    
    return redirect(url_for('admin.domains'))

@bp.route('/unblock_domain/<int:block_id>', methods=['POST'])
@login_required
def unblock_domain(block_id):
    blocked = BlockedDomain.query.get_or_404(block_id)
    domain = blocked.domain
    
    try:
        db.session.delete(blocked)
        db.session.commit()
        flash(f'Domain {domain} has been unblocked', 'success')
        logger.info(f"Admin {current_user.username} unblocked domain {domain}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unblocking domain: {str(e)}")
        flash('An error occurred while unblocking the domain', 'danger')
    
    return redirect(url_for('admin.domains'))

@bp.route('/scans')
@login_required
def scans():
    page = request.args.get('page', 1, type=int)
    scans = ScanHistory.query.order_by(ScanHistory.scan_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/scans.html', scans=scans)

@bp.route('/view_scan/<int:scan_id>')
@login_required
def view_scan(scan_id):
    scan = ScanHistory.query.get_or_404(scan_id)
    return render_template('admin/view_scan.html', scan=scan)

@bp.route('/make_admin', methods=['POST'])
@login_required
def make_admin():
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash(f'User {user.username} is already an admin', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.is_admin = True
        admin_profile = AdminUser(user_id=user.id)
        db.session.add(admin_profile)
        db.session.commit()
        flash(f'User {user.username} is now an admin', 'success')
        logger.info(f"Admin {current_user.username} promoted user {user.username} to admin")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error making user admin: {str(e)}")
        flash('An error occurred', 'danger')
    
    return redirect(url_for('admin.users'))

@bp.route('/remove_admin', methods=['POST'])
@login_required
def remove_admin():
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent removing yourself as admin
    if user_id == current_user.id:
        flash('You cannot remove your own admin privileges', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    
    if not user.is_admin:
        flash(f'User {user.username} is not an admin', 'warning')
        return redirect(url_for('admin.users'))
    
    try:
        user.is_admin = False
        admin_profile = AdminUser.query.filter_by(user_id=user.id).first()
        if admin_profile:
            db.session.delete(admin_profile)
        db.session.commit()
        flash(f'Admin privileges removed from {user.username}', 'success')
        logger.info(f"Admin {current_user.username} removed admin privileges from {user.username}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing admin privileges: {str(e)}")
        flash('An error occurred', 'danger')
    
    return redirect(url_for('admin.users'))

@bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    # Daily scans for the past 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Generate dates for the past 30 days
    date_labels = []
    scan_counts = []
    current_date = thirty_days_ago
    
    while current_date < datetime.utcnow():
        date_str = current_date.strftime('%Y-%m-%d')
        date_labels.append(date_str)
        
        next_date = current_date + timedelta(days=1)
        
        # Count scans for this day
        count = ScanHistory.query.filter(
            ScanHistory.scan_date >= current_date,
            ScanHistory.scan_date < next_date
        ).count()
        
        scan_counts.append(count)
        current_date = next_date
    
    # Risk distribution data
    risk_data = {
        'High Risk': ScanHistory.query.filter_by(risk_level='High Risk').count(),
        'Medium Risk': ScanHistory.query.filter_by(risk_level='Medium Risk').count(),
        'Low Risk': ScanHistory.query.filter_by(risk_level='Low Risk').count()
    }
    
    return jsonify({
        'daily_scans': {
            'labels': date_labels,
            'data': scan_counts
        },
        'risk_distribution': {
            'labels': list(risk_data.keys()),
            'data': list(risk_data.values())
        }
    })
