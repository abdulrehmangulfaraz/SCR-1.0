import os
import socket
import logging
import threading
import ipaddress
import requests
import json
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
from urllib.parse import urlparse
from flask import current_app
from app import app

logger = logging.getLogger(__name__)

def encrypt_data(data):
    """Encrypt data using the app's Fernet key"""
    if not data:
        return None
    
    fernet = current_app.config['FERNET']
    return fernet.encrypt(data.encode())

def decrypt_data(encrypted_data):
    """Decrypt data using the app's Fernet key"""
    if not encrypted_data:
        return None
    
    fernet = current_app.config['FERNET']
    try:
        return fernet.decrypt(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Decryption error: {str(e)}")
        return None

def is_valid_domain(domain):
    """Check if a string is a valid domain name"""
    if not domain:
        return False
    
    # Add http:// if no scheme is provided for urlparse
    if not domain.startswith(('http://', 'https://')):
        domain = 'http://' + domain
    
    try:
        result = urlparse(domain)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_domain(url):
    """Extract domain from URL"""
    if not url:
        return None
        
    # Add http:// if no scheme is provided
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
            
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain: {str(e)}")
        return None

def normalize_url(url):
    """Normalize URL with scheme"""
    if not url:
        return None
        
    if not url.startswith(('http://', 'https://')):
        # Default to http if no scheme provided
        return 'http://' + url
    
    return url

def get_risk_level(score):
    """Convert risk score to risk level"""
    if score <= 3:
        return "Low Risk"
    elif score <= 6:
        return "Medium Risk"
    else:
        return "High Risk"

def is_blocked_domain(domain):
    """Check if domain is in the blocked list"""
    from models import BlockedDomain
    
    if not domain:
        return False, None
    
    # Extract domain from URL if necessary
    domain = extract_domain(domain) or domain
    
    blocked = BlockedDomain.query.filter_by(domain=domain).first()
    if blocked:
        return True, blocked.reason
    
    return False, None

def is_private_ip(ip):
    """Check if an IP address is private"""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

def format_scan_result(result, duration=None):
    """Format scan results for display and storage"""
    formatted = {
        'domain': result.get('domain', 'Unknown'),
        'ip': result.get('ip_info', {}).get('ip', 'Unknown'),
        'risk_score': result.get('risk_score', 0),
        'risk_level': result.get('risk_level', 'Unknown'),
        'scan_duration': duration,
        'timestamp': result.get('timestamp', 'Unknown'),
        'vulnerabilities': result.get('vulnerabilities', []),
        'reconnaissance': {
            'whois': result.get('whois_data', {}),
            'dns_records': result.get('dns_records', []),
            'geo_ip': result.get('ip_info', {}).get('geo', {}),
            'open_ports': result.get('open_ports', [])
        }
    }
    
    return formatted

def safe_request(url, method='get', timeout=10, **kwargs):
    """Make a safe HTTP request with error handling"""
    try:
        if method.lower() == 'post':
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            response = requests.get(url, timeout=timeout, **kwargs)
        
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {str(e)}")
        return None
