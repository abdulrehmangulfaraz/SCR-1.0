#!/usr/bin/env python3
"""
Admin User Creation Script for SCR Platform
Run this script to create or promote a user to admin
"""

import os
import sys
from app import app, db
from models import User, AdminUser
from werkzeug.security import generate_password_hash

def create_new_admin(username, email, password):
    """Create a completely new admin user"""
    with app.app_context():
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"User {username} already exists. Use promote_to_admin instead.")
            return False
            
        # Create new user with admin privileges
        password_hash = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create admin profile
        admin_profile = AdminUser(user_id=new_user.id)
        db.session.add(admin_profile)
        db.session.commit()
        
        print(f"Created new admin user: {username}")
        return True

def promote_to_admin(username):
    """Promote existing user to admin"""
    with app.app_context():
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User {username} not found")
            return False
            
        # Check if already admin
        if user.is_admin:
            print(f"User {username} is already an admin")
            return False
            
        # Update user and create admin profile
        user.is_admin = True
        admin_profile = AdminUser(user_id=user.id)
        db.session.add(admin_profile)
        db.session.commit()
        
        print(f"User {username} is now an admin")
        return True

def list_users():
    """List all users in the system"""
    with app.app_context():
        users = User.query.all()
        print("\nAvailable users:")
        print("-" * 40)
        for user in users:
            admin_status = "ADMIN" if user.is_admin else "User"
            print(f"{user.username} | {user.email} | {admin_status}")
        print("-" * 40)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  List users: python create_admin.py list")
        print("  Create new admin: python create_admin.py create [username] [email] [password]")
        print("  Promote user: python create_admin.py promote [username]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    elif command == "create" and len(sys.argv) == 5:
        create_new_admin(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "promote" and len(sys.argv) == 3:
        promote_to_admin(sys.argv[2])
    else:
        print("Invalid command or missing arguments")
        print("Usage:")
        print("  List users: python create_admin.py list")
        print("  Create new admin: python create_admin.py create [username] [email] [password]")
        print("  Promote user: python create_admin.py promote [username]")