from datetime import datetime
from flask_login import UserMixin
from app import db
import os
from sqlalchemy.types import JSON as SQLAlchemyJSON, TypeDecorator, VARCHAR
import json

# Custom JSON type to handle different database dialects
class JSONType(TypeDecorator):
    """Platform-independent JSON type for multiple database backends."""
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

# Determine JSON column type based on database engine
database_url = os.environ.get("MYSQL_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
if "mysql" in database_url:
    JSON = JSONType
elif "postgresql" in database_url or "postgres" in database_url:
    JSON = SQLAlchemyJSON
else:
    # SQLite fallback
    from sqlalchemy.dialects.sqlite import JSON

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    encrypted_email = db.Column(db.LargeBinary, nullable=True)
    encrypted_username = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    scans = db.relationship('ScanHistory', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.username}>'

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='admin_profile', lazy=True)
    
    def __repr__(self):
        return f'<AdminUser {self.user.username}>'

class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    encrypted_domain = db.Column(db.LargeBinary, nullable=True)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    scan_results = db.Column(JSON, nullable=True)
    encrypted_results = db.Column(db.LargeBinary, nullable=True)
    report_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<ScanHistory {self.domain} ({self.scan_date})>'

class BlockedDomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    # Set specific length for MySQL compatibility (TEXT in MySQL can be up to 65,535 bytes)
    reason = db.Column(db.String(2000), nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    admin = db.relationship('User', backref='blocked_domains', lazy=True)
    
    def __repr__(self):
        return f'<BlockedDomain {self.domain}>'

class ScanStatistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    scan_count = db.Column(db.Integer, default=1)
    last_scanned = db.Column(db.DateTime, default=datetime.utcnow)
    avg_risk_score = db.Column(db.Float, nullable=True)
    
    def __repr__(self):
        return f'<ScanStatistics {self.domain} (scanned {self.scan_count} times)>'
