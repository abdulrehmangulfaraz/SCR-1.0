#!/usr/bin/env python3
"""
MySQL Database Setup Helper for SCR Platform

This script helps users set up a MySQL database connection 
for the Secure Cyber Reconnaissance platform.

Usage:
    python mysql_setup.py --host localhost --user username --password password --database scr_platform

The script will:
1. Test the MySQL connection
2. Create the database if it doesn't exist
3. Set up the MYSQL_DATABASE_URL environment variable
"""

import argparse
import os
import sys
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up MySQL database for SCR Platform")
    parser.add_argument("--host", default="localhost", help="MySQL server host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL server port")
    parser.add_argument("--user", required=True, help="MySQL username")
    parser.add_argument("--password", required=True, help="MySQL password") 
    parser.add_argument("--database", default="scr_platform", help="Database name")
    
    args = parser.parse_args()
    
    try:
        # Attempt to import MySQLdb or pymysql
        try:
            import pymysql
            logger.info("Using PyMySQL as MySQL driver")
            driver = "pymysql"
        except ImportError:
            logger.error("PyMySQL not found. Please install it with 'pip install pymysql'")
            sys.exit(1)
            
        # Construct MySQL connection URL
        # MySQL connection URL format: mysql+pymysql://username:password@host:port/database
        password = quote_plus(args.password)
        mysql_url = f"mysql+{driver}://{args.user}:{password}@{args.host}:{args.port}/{args.database}"
        
        # Test the connection and create database if needed
        try:
            # Connect to the MySQL server
            conn = pymysql.connect(
                host=args.host,
                port=args.port,
                user=args.user,
                password=args.password
            )
            cursor = conn.cursor()
            
            # Check if database exists, create if it doesn't
            cursor.execute(f"SHOW DATABASES LIKE '{args.database}'")
            if not cursor.fetchone():
                logger.info(f"Creating database '{args.database}'...")
                cursor.execute(f"CREATE DATABASE {args.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info(f"Database '{args.database}' created successfully")
            else:
                logger.info(f"Database '{args.database}' already exists")
                
            # Close the cursor and connection
            cursor.close()
            conn.close()
            
            # Set environment variable for the application
            logger.info(f"MySQL connection successful. Setting MYSQL_DATABASE_URL environment variable.")
            
            # Print instructions for setting the environment variable
            print("\n=== MySQL Database Setup Complete ===")
            print("\nTo use MySQL with the SCR Platform, set the following environment variable:")
            print(f"MYSQL_DATABASE_URL={mysql_url}")
            print("\nIn your .env file or deployment environment.")
            print("\nFor local development, you can set this variable by running:")
            print(f"export MYSQL_DATABASE_URL='{mysql_url}'")
            
        except Exception as e:
            logger.error(f"Error connecting to MySQL: {str(e)}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()