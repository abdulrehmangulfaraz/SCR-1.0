import logging
import socket
import whois
import dns.resolver
import threading
import json
import requests
import nmap3
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def perform_reconnaissance(url):
    """
    Perform reconnaissance on a target domain
    
    Args:
        url (str): Target URL or domain
        
    Returns:
        dict: Reconnaissance results including IP, WHOIS, DNS, GeoIP, and open ports
    """
    logger.info(f"Starting reconnaissance for {url}")
    
    # Parse the URL to extract the domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # Remove port number if present
    if ":" in domain:
        domain = domain.split(":")[0]
    
    results = {
        "domain": domain,
        "url": url,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Get IP address
        ip_info = get_ip_info(domain)
        results["ip_info"] = ip_info
        
        # Get WHOIS data
        whois_data = get_whois_data(domain)
        results["whois_data"] = whois_data
        
        # Get DNS records
        dns_records = get_dns_records(domain)
        results["dns_records"] = dns_records
        
        # Scan for open ports
        open_ports = scan_ports(domain)
        results["open_ports"] = open_ports
        
        logger.info(f"Reconnaissance completed for {domain}")
        return results
        
    except Exception as e:
        logger.error(f"Error during reconnaissance: {str(e)}")
        results["error"] = str(e)
        return results

def get_ip_info(domain):
    """Get IP address and GeoIP information for a domain"""
    try:
        # Get IP address
        ip_address = socket.gethostbyname(domain)
        
        # Get GeoIP information
        geo_data = get_geoip_data(ip_address)
        
        return {
            "ip": ip_address,
            "geo": geo_data
        }
    except socket.gaierror as e:
        logger.error(f"IP lookup error for {domain}: {str(e)}")
        return {"ip": "Not found", "geo": {}}
    except Exception as e:
        logger.error(f"Error getting IP info: {str(e)}")
        return {"ip": "Error", "geo": {}}

def get_geoip_data(ip):
    """Get geographical information for an IP address using ip-api.com"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country", "Unknown"),
                    "country_code": data.get("countryCode", "Unknown"),
                    "region": data.get("regionName", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "zip": data.get("zip", "Unknown"),
                    "lat": data.get("lat", 0),
                    "lon": data.get("lon", 0),
                    "timezone": data.get("timezone", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "org": data.get("org", "Unknown"),
                    "as": data.get("as", "Unknown"),
                }
            return {"error": "GeoIP lookup failed"}
        return {"error": f"GeoIP API error: {response.status_code}"}
    except Exception as e:
        logger.error(f"GeoIP lookup error: {str(e)}")
        return {"error": str(e)}

def get_whois_data(domain):
    """Get WHOIS information for a domain"""
    try:
        w = whois.whois(domain)
        
        # Convert dates to ISO format
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            creation_date = creation_date.isoformat() if hasattr(creation_date, 'isoformat') else str(creation_date)
            
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]
        if expiration_date:
            expiration_date = expiration_date.isoformat() if hasattr(expiration_date, 'isoformat') else str(expiration_date)
        
        updated_date = w.updated_date
        if isinstance(updated_date, list):
            updated_date = updated_date[0]
        if updated_date:
            updated_date = updated_date.isoformat() if hasattr(updated_date, 'isoformat') else str(updated_date)
            
        # Format the result
        whois_result = {
            "domain_name": w.domain_name,
            "registrar": w.registrar,
            "creation_date": creation_date,
            "expiration_date": expiration_date,
            "updated_date": updated_date,
            "name_servers": w.name_servers,
            "status": w.status,
            "emails": w.emails,
            "dnssec": getattr(w, "dnssec", "Unknown")
        }
        
        # Filter out None values
        return {k: v for k, v in whois_result.items() if v is not None}
    except Exception as e:
        logger.error(f"WHOIS lookup error for {domain}: {str(e)}")
        return {"error": str(e)}

def get_dns_records(domain):
    """Get DNS records for a domain"""
    dns_records = []
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
    
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for rdata in answers:
                record = {
                    "type": record_type,
                    "value": str(rdata)
                }
                dns_records.append(record)
        except dns.resolver.NoAnswer:
            continue
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist")
            break
        except Exception as e:
            logger.error(f"Error getting {record_type} records for {domain}: {str(e)}")
    
    return dns_records

def scan_ports(target, ports=None):
    """
    Scan for open ports on the target
    
    Args:
        target (str): Target domain or IP
        ports (list): List of ports to scan, defaults to common ports
        
    Returns:
        list: Open ports with service information
    """
    if ports is None:
        # Common ports to scan
        ports = [21, 22, 23, 25, 53, 80, 110, 123, 143, 443, 465, 587, 993, 995, 3306, 3389, 5432, 8080, 8443]
    
    open_ports = []
    
    try:
        # Use python-nmap for port scanning
        nmap = nmap3.Nmap()
        results = nmap.scan_top_ports(target, args="-T4 --max-retries 1 --host-timeout 30s")
        
        if target in results:
            ports_info = results[target].get('ports', [])
            for port_info in ports_info:
                if port_info.get('state', {}).get('state') == 'open':
                    open_ports.append({
                        'port': int(port_info.get('portid', 0)),
                        'protocol': port_info.get('protocol', 'tcp'),
                        'service': port_info.get('service', {}).get('name', 'unknown'),
                        'state': 'open'
                    })
    except Exception as e:
        logger.error(f"Port scanning error: {str(e)}")
        
        # Fallback to basic socket scanning if nmap fails
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((target, port))
                if result == 0:
                    service = socket.getservbyport(port) if port < 1024 else "unknown"
                    open_ports.append({
                        'port': port,
                        'protocol': 'tcp',
                        'service': service,
                        'state': 'open'
                    })
                sock.close()
            except:
                continue
    
    return open_ports
