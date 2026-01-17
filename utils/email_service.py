"""
Email Service
=============
Send email notifications to users
"""

import os
from threading import Thread
from flask import current_app, render_template_string


# Email templates
TEMPLATES = {
    'report_status_changed': {
        'subject': 'Your Accident Report Status Has Changed',
        'body': '''
Hello {{ name }},

Your accident report #{{ report_id }} status has been updated to: {{ status }}

{% if message %}
Message from administrator:
{{ message }}
{% endif %}

View your report: {{ report_url }}

Best regards,
Traffic Accident System
'''
    },
    'new_accident_alert': {
        'subject': 'New Accident Reported in {{ location }}',
        'body': '''
Hello {{ name }},

A new accident has been reported in your area:

Location: {{ location }}
Date: {{ date }}
Severity: {{ severity }}

View details: {{ accident_url }}

Stay safe,
Traffic Accident System
'''
    },
    'weekly_summary': {
        'subject': 'Weekly Accident Summary - {{ week }}',
        'body': '''
Hello {{ name }},

Here's your weekly accident summary:

Total Accidents This Week: {{ total_accidents }}
Severe Accidents: {{ severe_count }}
Most Affected Area: {{ top_location }}

{% if top_causes %}
Top Causes:
{% for cause in top_causes %}
- {{ cause.name }}: {{ cause.count }}
{% endfor %}
{% endif %}

View full statistics: {{ stats_url }}

Best regards,
Traffic Accident System
'''
    },
    'welcome': {
        'subject': 'Welcome to Traffic Accident System',
        'body': '''
Hello {{ name }},

Welcome to the Traffic Accident Information System!

Your account has been created successfully.

You can now:
- Report accidents
- View accident statistics
- Track your reports

Login here: {{ login_url }}

Best regards,
Traffic Accident System
'''
    },
    '2fa_code': {
        'subject': 'Your Verification Code',
        'body': '''
Hello {{ name }},

Your verification code is: {{ code }}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Traffic Accident System
'''
    }
}


class EmailService:
    """Email service with SMTP support"""
    
    def __init__(self, app=None):
        self.app = app
        self.enabled = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Check for email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@traffic-system.com')
        
        self.enabled = bool(self.smtp_user and self.smtp_password)
        
        if not self.enabled:
            print("Email service disabled: SMTP_USER and SMTP_PASSWORD not configured")
    
    def send_email(self, to_email, subject, body, html_body=None):
        """Send an email (async by default)"""
        if not self.enabled:
            print(f"[EMAIL DEMO] To: {to_email}, Subject: {subject}")
            print(f"Body: {body[:200]}...")
            return True
        
        # Send in background thread
        thread = Thread(target=self._send_email_sync, 
                       args=(to_email, subject, body, html_body))
        thread.start()
        return True
    
    def _send_email_sync(self, to_email, subject, body, html_body=None):
        """Synchronous email sending"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def send_template(self, to_email, template_name, **context):
        """Send email using a template"""
        template = TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Render subject and body
        subject = render_template_string(template['subject'], **context)
        body = render_template_string(template['body'], **context)
        
        return self.send_email(to_email, subject, body)
    
    def send_report_status_change(self, to_email, name, report_id, status, message=None, report_url=None):
        """Send report status change notification"""
        return self.send_template(
            to_email, 
            'report_status_changed',
            name=name,
            report_id=report_id,
            status=status,
            message=message,
            report_url=report_url or '#'
        )
    
    def send_welcome(self, to_email, name, login_url=None):
        """Send welcome email"""
        return self.send_template(
            to_email,
            'welcome',
            name=name,
            login_url=login_url or '#'
        )
    
    def send_2fa_code(self, to_email, name, code):
        """Send 2FA verification code"""
        return self.send_template(
            to_email,
            '2fa_code',
            name=name,
            code=code
        )


# Global instance
email_service = EmailService()
