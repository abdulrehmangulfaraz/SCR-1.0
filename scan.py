import logging
import json
import time
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from models import ScanHistory, BlockedDomain, ScanStatistics
from utils import is_valid_domain, extract_domain, normalize_url, is_blocked_domain
from reconnaissance import perform_reconnaissance
from vulnerability_scanner import perform_vulnerability_scan
from report import generate_report
from utils import encrypt_data, format_scan_result, get_risk_level

bp = Blueprint('scan', __name__)
logger = logging.getLogger(__name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent scans for the user
    recent_scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scan_date.desc()).limit(5).all()
    
    # Calculate statistics
    total_scans = ScanHistory.query.filter_by(user_id=current_user.id).count()
    
    high_risk_scans = ScanHistory.query.filter_by(user_id=current_user.id, risk_level='High Risk').count()
    medium_risk_scans = ScanHistory.query.filter_by(user_id=current_user.id, risk_level='Medium Risk').count()
    low_risk_scans = ScanHistory.query.filter_by(user_id=current_user.id, risk_level='Low Risk').count()
    
    stats = {
        'total_scans': total_scans,
        'high_risk': high_risk_scans,
        'medium_risk': medium_risk_scans,
        'low_risk': low_risk_scans
    }
    
    return render_template('dashboard.html', recent_scans=recent_scans, stats=stats)

@bp.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        target_domain = request.form.get('domain', '').strip()
        scan_type = request.form.get('scan_type', 'full')
        
        if not target_domain:
            flash('Please enter a valid domain', 'danger')
            return redirect(url_for('scan.scan'))
        
        if not is_valid_domain(target_domain):
            flash('Invalid domain format', 'danger')
            return redirect(url_for('scan.scan'))
        
        # Extract the domain if user entered a URL
        domain = extract_domain(target_domain) or target_domain
        
        # Check if domain is blocked
        is_blocked, reason = is_blocked_domain(domain)
        if is_blocked:
            flash(f'This domain has been blocked by administrators. Reason: {reason}', 'danger')
            return redirect(url_for('scan.scan'))
        
        # Create a normalized URL for scanning
        normalized_url = normalize_url(target_domain)
        
        # Start scan process
        return redirect(url_for('scan.perform_scan', domain=normalized_url, scan_type=scan_type))
    
    return render_template('scan.html')

@bp.route('/perform_scan')
@login_required
def perform_scan():
    target_domain = request.args.get('domain', '')
    scan_type = request.args.get('scan_type', 'full')
    
    if not target_domain:
        flash('Please enter a valid domain', 'danger')
        return redirect(url_for('scan.scan'))
    
    # Extract the domain if user entered a URL
    domain = extract_domain(target_domain)
    
    return render_template('scan.html', target_domain=target_domain, scan_type=scan_type, scanning=True)

@bp.route('/api/scan', methods=['POST'])
@login_required
def api_scan():
    from flask import Response, stream_with_context
    
    data = request.json
    target_domain = data.get('domain', '').strip()
    scan_type = data.get('scan_type', 'full')
    
    if not target_domain:
        return jsonify({'status': 'error', 'message': 'Please enter a valid domain'}), 400
    
    if not is_valid_domain(target_domain):
        return jsonify({'status': 'error', 'message': 'Invalid domain format'}), 400
    
    # Extract the domain if user entered a URL
    domain = extract_domain(target_domain) or target_domain
    
    # Check if domain is blocked
    is_blocked, reason = is_blocked_domain(domain)
    if is_blocked:
        return jsonify({
            'status': 'error', 
            'message': f'This domain has been blocked by administrators. Reason: {reason}'
        }), 403
    
    # Create a normalized URL for scanning
    normalized_url = normalize_url(target_domain)
    
    def generate():
        # Record start time
        start_time = time.time()
        
        try:
            # Initial progress update
            yield json.dumps({
                'status': 'progress',
                'stage': 'initialization',
                'progress': 10,
                'message': 'Starting reconnaissance...'
            }) + '\n'
            
            # Step 1: Perform reconnaissance
            recon_results = perform_reconnaissance(normalized_url)
            
            # Reconnaissance progress update
            yield json.dumps({
                'status': 'progress',
                'stage': 'reconnaissance',
                'progress': 50,
                'message': 'Reconnaissance completed, starting vulnerability scan...'
            }) + '\n'
            
            # Step 2: Perform vulnerability scan
            vuln_results = perform_vulnerability_scan(normalized_url, scan_type)
            
            # Vulnerability scan progress update
            yield json.dumps({
                'status': 'progress',
                'stage': 'vulnerability_scan',
                'progress': 80,
                'message': 'Vulnerability scan completed, generating results...'
            }) + '\n'
            
            # Step 3: Calculate risk score
            risk_score = 0
            vulnerabilities = []
            
            # Add scores for vulnerabilities
            if vuln_results.get('sql_injection'):
                risk_score += 4
                vulnerabilities.append({
                    'type': 'SQL Injection',
                    'severity': 'High',
                    'description': 'Application is vulnerable to SQL injection attacks',
                    'details': vuln_results.get('sql_injection_details', 'Possible SQL injection vulnerability detected')
                })
            
            if vuln_results.get('xss'):
                risk_score += 3
                vulnerabilities.append({
                    'type': 'Cross-Site Scripting (XSS)',
                    'severity': 'High',
                    'description': 'Application is vulnerable to cross-site scripting attacks',
                    'details': vuln_results.get('xss_details', 'Possible XSS vulnerability detected')
                })
            
            if vuln_results.get('missing_headers'):
                risk_score += 2
                vulnerabilities.append({
                    'type': 'Missing Security Headers',
                    'severity': 'Medium',
                    'description': 'Application is missing important security headers',
                    'details': 'Missing headers: ' + ', '.join(vuln_results.get('missing_headers', []))
                })
            
            # Add scores for open ports
            open_ports = recon_results.get('open_ports', [])
            for port in open_ports:
                if port['port'] in [21, 22, 23, 3389]:  # FTP, SSH, Telnet, RDP
                    risk_score += 1
                    vulnerabilities.append({
                        'type': f"Open {port['service']} Port",
                        'severity': 'Medium',
                        'description': f"Port {port['port']} ({port['service']}) is open",
                        'details': f"Open {port['service']} port could potentially be exploited if not properly secured"
                    })
            
            # Calculate risk level
            risk_level = get_risk_level(risk_score)
            
            # Calculate scan duration
            duration = time.time() - start_time
            
            # Prepare scan results
            scan_result = {
                'domain': domain,
                'url': normalized_url,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_info': recon_results.get('ip_info', {}),
                'whois_data': recon_results.get('whois_data', {}),
                'dns_records': recon_results.get('dns_records', []),
                'open_ports': open_ports,
                'vulnerabilities': vulnerabilities,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'scan_duration': f"{duration:.2f} seconds"
            }
            
            # Format results for display and storage
            formatted_result = format_scan_result(scan_result, f"{duration:.2f} seconds")
            
            # Encrypt sensitive scan results
            encrypted_results = encrypt_data(json.dumps(formatted_result))
            encrypted_domain = encrypt_data(domain)
            
            # Save scan to database
            scan_history = ScanHistory(
                user_id=current_user.id,
                domain=domain,
                encrypted_domain=encrypted_domain,
                scan_date=datetime.utcnow(),
                risk_score=risk_score,
                risk_level=risk_level,
                scan_results=formatted_result,
                encrypted_results=encrypted_results
            )
            
            db.session.add(scan_history)
            
            # Update scan statistics
            stat = ScanStatistics.query.filter_by(domain=domain).first()
            if stat:
                stat.scan_count += 1
                stat.last_scanned = datetime.utcnow()
                # Update average risk score
                stat.avg_risk_score = ((stat.avg_risk_score * (stat.scan_count - 1)) + risk_score) / stat.scan_count
            else:
                stat = ScanStatistics(
                    domain=domain,
                    scan_count=1,
                    last_scanned=datetime.utcnow(),
                    avg_risk_score=risk_score
                )
                db.session.add(stat)
                
            db.session.commit()
            
            # Generate PDF report
            report_path = generate_report(scan_history.id)
            if report_path:
                scan_history.report_path = report_path
                db.session.commit()
            
            # Complete progress update
            yield json.dumps({
                'status': 'complete',
                'progress': 100,
                'message': 'Scan completed successfully',
                'scan_id': scan_history.id,
                'result': formatted_result
            }) + '\n'
            
        except Exception as e:
            logger.error(f"Scan error: {str(e)}")
            yield json.dumps({
                'status': 'error',
                'message': f'An error occurred during the scan: {str(e)}'
            }) + '\n'
    
    return Response(stream_with_context(generate()), 
                    mimetype='text/event-stream',
                    headers={'X-Accel-Buffering': 'no',
                             'Cache-Control': 'no-cache',
                             'Connection': 'keep-alive'})

@bp.route('/api/scan_status/<int:scan_id>')
@login_required
def scan_status(scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    
    if not scan:
        return jsonify({'status': 'error', 'message': 'Scan not found'}), 404
    
    return jsonify({
        'status': 'complete',
        'scan_id': scan.id,
        'domain': scan.domain,
        'scan_date': scan.scan_date.isoformat(),
        'risk_score': scan.risk_score,
        'risk_level': scan.risk_level,
        'result': scan.scan_results
    })

@bp.route('/scan_result/<int:scan_id>')
@login_required
def scan_result(scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    
    if not scan:
        flash('Scan not found', 'danger')
        return redirect(url_for('scan.history'))
    
    return render_template('report.html', scan=scan)

@bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    scans = ScanHistory.query.filter_by(user_id=current_user.id).order_by(ScanHistory.scan_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('history.html', scans=scans)

@bp.route('/delete_scan/<int:scan_id>', methods=['POST'])
@login_required
def delete_scan(scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    
    if not scan:
        flash('Scan not found', 'danger')
        return redirect(url_for('scan.history'))
    
    try:
        db.session.delete(scan)
        db.session.commit()
        flash('Scan deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting scan: {str(e)}")
        flash('An error occurred while deleting the scan', 'danger')
    
    return redirect(url_for('scan.history'))

@bp.route('/rescan/<int:scan_id>')
@login_required
def rescan(scan_id):
    scan = ScanHistory.query.filter_by(id=scan_id, user_id=current_user.id).first()
    
    if not scan:
        flash('Scan not found', 'danger')
        return redirect(url_for('scan.history'))
    
    return redirect(url_for('scan.perform_scan', domain=scan.domain, scan_type='full'))
