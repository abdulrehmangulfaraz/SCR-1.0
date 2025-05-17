import logging
from werkzeug.security import generate_password_hash
from app import db
from models import User, AdminUser

logger = logging.getLogger(__name__)

def create_superadmin():
    """
    Create a hardcoded super admin user on application startup if it doesn't exist.
    This ensures there's always an admin account available.
    """
    # Super admin user details
    ADMIN_USERNAME = "superadmin"
    ADMIN_EMAIL = "superadmin@securecyber.com" 
    ADMIN_PASSWORD = "Abdulrehman@123!" 
    
    try:
        # Check if admin already exists
        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        
        if admin:
            logger.info(f"Super admin {ADMIN_USERNAME} already exists")
            
            # Make sure the user is an admin
            if not admin.is_admin:
                admin.is_admin = True
                
                # Check if admin profile exists
                admin_profile = AdminUser.query.filter_by(user_id=admin.id).first()
                if not admin_profile:
                    admin_profile = AdminUser(user_id=admin.id)
                    db.session.add(admin_profile)
                    
                db.session.commit()
                logger.info(f"Promoted {ADMIN_USERNAME} to admin")
            else:
                logger.info(f"{ADMIN_USERNAME} is already an admin")
        else:
            # Create new admin user
            password_hash = generate_password_hash(ADMIN_PASSWORD)
            new_admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=password_hash,
                is_admin=True
            )
            db.session.add(new_admin)
            db.session.commit()
            
            # Create admin profile
            admin_profile = AdminUser(user_id=new_admin.id)
            db.session.add(admin_profile)
            db.session.commit()
            
            logger.info(f"Created new super admin user: {ADMIN_USERNAME}")
            logger.info(f"Email: {ADMIN_EMAIL}")
            logger.info(f"Password: {ADMIN_PASSWORD}")
    except Exception as e:
        logger.error(f"Error creating super admin: {str(e)}")
        db.session.rollback()