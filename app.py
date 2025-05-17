import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create an SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
# Use MySQL for production if MY_SQL_DATABASE_URL is present, otherwise fallback to PostgreSQL/SQLite
mysql_url = os.environ.get("MYSQL_DATABASE_URL")
postgresql_url = os.environ.get("DATABASE_URL")

if mysql_url:
    # Configure MySQL with PyMySQL
    app.config["SQLALCHEMY_DATABASE_URI"] = mysql_url
    logger.info("Using MySQL database")
elif postgresql_url:
    # Use PostgreSQL if available
    app.config["SQLALCHEMY_DATABASE_URI"] = postgresql_url
    logger.info("Using PostgreSQL database")
else:
    # Fallback to SQLite for development
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scr.db"
    logger.info("Using SQLite database")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize cryptography key
if not os.environ.get('ENCRYPTION_KEY'):
    encryption_key = Fernet.generate_key()
    logger.info("Generated new encryption key")
else:
    encryption_key = os.environ.get('ENCRYPTION_KEY').encode()
    logger.info("Using existing encryption key")

app.config['ENCRYPTION_KEY'] = encryption_key
app.config['FERNET'] = Fernet(encryption_key)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

with app.app_context():
    # Import models to create tables
    from models import User, ScanHistory, BlockedDomain, AdminUser
    db.create_all()
    
    # Import routes after tables are created
    import auth
    import scan
    import admin
    import reconnaissance
    import vulnerability_scanner
    import report
    
    # Create default superadmin account
    from superadmin_setup import create_superadmin
    create_superadmin()
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(scan.bp)
    app.register_blueprint(admin.bp)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
