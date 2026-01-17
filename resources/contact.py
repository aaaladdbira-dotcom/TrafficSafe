from flask import Blueprint, request, jsonify
from flask_limiter.util import get_remote_address
from extensions import limiter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

contact_bp = Blueprint("contact", __name__, url_prefix="/api/contact")


@contact_bp.route("", methods=["POST"])
@limiter.limit("5 per hour;20 per day", key_func=get_remote_address)
def submit_contact():
    """Submit contact form and send email."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(key in data for key in ['name', 'email', 'subject', 'message']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Validate field lengths
        if not name or len(name) > 100:
            return jsonify({'error': 'Invalid name'}), 400
        if not email or len(email) > 255:
            return jsonify({'error': 'Invalid email'}), 400
        if not subject or len(subject) > 200:
            return jsonify({'error': 'Invalid subject'}), 400
        if not message or len(message) > 5000:
            return jsonify({'error': 'Invalid message'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Send email
        try:
            send_contact_email(name, email, subject, message)
            return jsonify({'success': True, 'message': 'Message sent successfully'}), 200
        except Exception as e:
            print(f"Error sending email: {e}")
            return jsonify({'error': 'Failed to send message. Please try again later.'}), 500
            
    except Exception as e:
        print(f"Error in submit_contact: {e}")
        return jsonify({'error': 'An error occurred'}), 500


def send_contact_email(name, email, subject, message):
    """Send contact form email."""
    # Get SMTP credentials from environment
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SENDER_EMAIL', 'trafficaccidentstn@gmail.com')
    sender_password = os.getenv('SENDER_PASSWORD', '')
    recipient_email = os.getenv('RECIPIENT_EMAIL', 'trafficaccidentstn@gmail.com')
    
    if not sender_password:
        raise Exception("SMTP credentials not configured")
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"Contact Form: {subject}"
    
    # Email body
    body = f"""
New Contact Form Submission

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
This is an automated message from TrafficSafe Contact Form
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
