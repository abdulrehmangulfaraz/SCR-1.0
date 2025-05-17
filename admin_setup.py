#!/usr/bin/env python3
from app import app, db
from models import User, AdminUser
from werkzeug.security import generate_password_hash

# Admin user details
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@securecyber.com" 
ADMIN_PASSWORD = "Admin123!"

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    
    if admin:
        print(f"User {ADMIN_USERNAME} already exists")
        
        # Make sure the user is an admin
        if not admin.is_admin:
            admin.is_admin = True
            
            # Check if admin profile exists
            admin_profile = AdminUser.query.filter_by(user_id=admin.id).first()
            if not admin_profile:
                admin_profile = AdminUser(user_id=admin.id)
                db.session.add(admin_profile)
                
            db.session.commit()
            print(f"Promoted {ADMIN_USERNAME} to admin")
        else:
            print(f"{ADMIN_USERNAME} is already an admin")
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
        
        print(f"Created new admin user: {ADMIN_USERNAME}")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
        
    # List all users
    print("\nAll users in the system:")
    users = User.query.all()
    for user in users:
        admin_status = "ADMIN" if user.is_admin else "User"
        print(f"{user.username} | {user.email} | {admin_status}")