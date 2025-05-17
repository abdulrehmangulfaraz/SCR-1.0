import os
import time
import logging
from datetime import datetime
from flask import current_app
import json
from models import ScanHistory, User
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

logger = logging.getLogger(__name__)

def generate_report(scan_id):
    """
    Generate a PDF report for a scan
    
    Args:
        scan_id (int): ID of the scan to generate report for
        
    Returns:
        str: Path to the generated PDF file, or None if an error occurs
    """
    try:
        # Get scan information from database
        scan = ScanHistory.query.get(scan_id)
        if not scan:
            logger.error(f"Scan with ID {scan_id} not found")
            return None
            
        user = User.query.get(scan.user_id)
        if not user:
            logger.error(f"User with ID {scan.user_id} not found")
            return None
        
        # Create directory for reports if it doesn't exist
        reports_dir = os.path.join(current_app.root_path, 'static', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create a unique filename
        timestamp = int(time.time())
        filename = f"SCR_Report_{scan.domain.replace('.', '_')}_{timestamp}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        # Create the PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = styles["Heading1"]
        title_style.alignment = 1  # Center
        
        subtitle_style = styles["Heading2"]
        subtitle_style.alignment = 1  # Center
        
        header_style = styles["Heading3"]
        
        normal_style = styles["Normal"]
        
        # Add custom paragraph style for vulnerabilities
        styles.add(ParagraphStyle(
            name='VulnHigh',
            parent=styles['Normal'],
            textColor=colors.red,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            name='VulnMedium',
            parent=styles['Normal'],
            textColor=colors.orange,
            spaceAfter=6
        ))
        
        styles.add(ParagraphStyle(
            name='VulnLow',
            parent=styles['Normal'],
            textColor=colors.green,
            spaceAfter=6
        ))
        
        # Start building the document
        elements = []
        
        # Add title and header information
        elements.append(Paragraph("Secure Cyber Reconnaissance", title_style))
        elements.append(Spacer(1, 0.25*inch))
        elements.append(Paragraph("Security Scan Report", subtitle_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Add scan information
        scan_date = scan.scan_date.strftime('%Y-%m-%d %H:%M:%S UTC')
        scan_data = [
            ["Domain", scan.domain],
            ["Scan Date", scan_date],
            ["Risk Score", f"{scan.risk_score}/10"],
            ["Risk Level", scan.risk_level]
        ]
        
        scan_table = Table(scan_data, colWidths=[2*inch, 4*inch])
        scan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        
        elements.append(scan_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add risk score visualization
        risk_score_data = {
            'High Risk': 0,
            'Medium Risk': 0,
            'Low Risk': 0
        }
        
        if scan.risk_level == 'High Risk':
            risk_score_data['High Risk'] = 1
        elif scan.risk_level == 'Medium Risk':
            risk_score_data['Medium Risk'] = 1
        else:
            risk_score_data['Low Risk'] = 1
        
        # Add vulnerabilities section
        elements.append(Paragraph("Vulnerabilities Found", header_style))
        elements.append(Spacer(1, 0.1*inch))
        
        scan_results = scan.scan_results
        vulnerabilities = scan_results.get('vulnerabilities', [])
        
        if vulnerabilities:
            for vuln in vulnerabilities:
                vuln_type = vuln.get('type', 'Unknown')
                severity = vuln.get('severity', 'Medium')
                description = vuln.get('description', '')
                details = vuln.get('details', '')
                
                if severity == 'High':
                    style = styles['VulnHigh']
                elif severity == 'Medium':
                    style = styles['VulnMedium']
                else:
                    style = styles['VulnLow']
                
                elements.append(Paragraph(f"<b>{vuln_type}</b> (Severity: {severity})", style))
                elements.append(Paragraph(f"<b>Description:</b> {description}", normal_style))
                elements.append(Paragraph(f"<b>Details:</b> {details}", normal_style))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No vulnerabilities were found.", normal_style))
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Add reconnaissance results
        elements.append(Paragraph("Reconnaissance Information", header_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # IP Information
        elements.append(Paragraph("IP Information", styles["Heading4"]))
        ip_address = scan_results.get('ip', 'Unknown')
        elements.append(Paragraph(f"<b>IP Address:</b> {ip_address}", normal_style))
        
        # GeoIP Information
        geo_info = scan_results.get('reconnaissance', {}).get('geo_ip', {})
        if geo_info and not geo_info.get('error'):
            geo_data = [
                ["Country", geo_info.get('country', 'Unknown')],
                ["City", geo_info.get('city', 'Unknown')],
                ["Region", geo_info.get('region', 'Unknown')],
                ["ISP", geo_info.get('isp', 'Unknown')],
                ["Organization", geo_info.get('org', 'Unknown')]
            ]
            
            geo_table = Table(geo_data, colWidths=[2*inch, 4*inch])
            geo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            elements.append(Spacer(1, 0.1*inch))
            elements.append(geo_table)
        
        # Open Ports
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("Open Ports", styles["Heading4"]))
        
        open_ports = scan_results.get('reconnaissance', {}).get('open_ports', [])
        if open_ports:
            port_data = [["Port", "Protocol", "Service"]]
            
            for port in open_ports:
                port_data.append([
                    str(port.get('port', 'Unknown')),
                    port.get('protocol', 'Unknown'),
                    port.get('service', 'Unknown')
                ])
            
            port_table = Table(port_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
            port_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            elements.append(port_table)
        else:
            elements.append(Paragraph("No open ports detected.", normal_style))
        
        # DNS Records
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("DNS Records", styles["Heading4"]))
        
        dns_records = scan_results.get('reconnaissance', {}).get('dns_records', [])
        if dns_records:
            dns_data = [["Type", "Value"]]
            
            for record in dns_records:
                dns_data.append([
                    record.get('type', 'Unknown'),
                    record.get('value', 'Unknown')
                ])
            
            dns_table = Table(dns_data, colWidths=[1*inch, 5*inch])
            dns_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            
            elements.append(dns_table)
        else:
            elements.append(Paragraph("No DNS records found.", normal_style))
        
        # Add footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Report generated by SCR on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", normal_style))
        elements.append(Paragraph("This report is confidential and intended for authorized use only.", normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        # Return the relative path for storage in the database
        relative_path = os.path.join('static', 'reports', filename)
        return relative_path
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return None
