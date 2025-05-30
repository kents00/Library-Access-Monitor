import random
import string
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

# Store verification codes in memory (in production, use Redis or database)
password_reset_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification code via email"""
    try:
        # Email configuration - get from environment variables
        smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('MAIL_PORT', 587)
        sender_email = current_app.config.get('MAIL_USERNAME')
        sender_password = current_app.config.get('MAIL_PASSWORD')

        # Check if email credentials are configured
        if not sender_email or not sender_password:
            current_app.logger.warning("Email credentials not configured")
            if current_app.config.get('DEBUG', False):
                current_app.logger.info(f"DEBUG MODE: Would send code {code} to {email}")
                # In debug mode without email config, show the code in flash message
                return True
            return False

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Verification Code - Library Access Monitor"
        message["From"] = sender_email
        message["To"] = email

        # Create HTML content
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0d6efd; text-align: center;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>You have requested to reset your password for the Library Access Monitor Admin Panel.</p>
                <p>Your verification code is:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: bold; background-color: #f8f9fa; padding: 15px 30px; border-radius: 8px; letter-spacing: 5px; color: #0d6efd;">{code}</span>
                </div>
                <p>This code will expire in 10 minutes for security reasons.</p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated message from the Library Access Monitor System.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        # Create plain text version
        text = f"""
        Password Reset Request - Library Access Monitor

        Hello,

        You have requested to reset your password for the Library Access Monitor Admin Panel.

        Your verification code is: {code}

        This code will expire in 10 minutes for security reasons.

        If you didn't request this password reset, please ignore this email.

        ---
        This is an automated message from the Library Access Monitor System.
        Please do not reply to this email.
        """

        # Add both parts to message
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        # Try to send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())

            current_app.logger.info(f"Verification email sent successfully to {email}")
            return True

        except (ConnectionError, OSError, smtplib.SMTPException) as e:
            current_app.logger.error(f"Network/SMTP error sending email: {str(e)}")

            # In debug mode, if email fails, still show the code for testing
            if current_app.config.get('DEBUG', False):
                current_app.logger.info(f"DEBUG MODE: Email failed, but code is {code} for {email}")
                return True
            return False

    except Exception as e:
        current_app.logger.error(f"Error sending email: {str(e)}")

        # In debug mode, if there's any error, still show the code for testing
        if current_app.config.get('DEBUG', False):
            current_app.logger.info(f"DEBUG MODE: Email error, but code is {code} for {email}")
            return True
        return False

def store_verification_code(email, code):
    """Store verification code with timestamp"""
    password_reset_codes[email] = {
        'code': code,
        'timestamp': datetime.now(),
        'attempts': 0
    }

def verify_code(email, entered_code):
    """Verify the entered code"""
    if email not in password_reset_codes:
        return False, 'Verification code has expired. Please request a new one.'

    code_data = password_reset_codes[email]

    # Check if code has expired (10 minutes)
    if datetime.now() - code_data['timestamp'] > timedelta(minutes=10):
        del password_reset_codes[email]
        return False, 'Verification code has expired. Please request a new one.'

    # Check attempts (max 3 attempts)
    if code_data['attempts'] >= 3:
        del password_reset_codes[email]
        return False, 'Too many failed attempts. Please request a new verification code.'

    # Verify code
    if entered_code == code_data['code']:
        return True, 'Code verified successfully.'
    else:
        # Increment attempts
        password_reset_codes[email]['attempts'] += 1
        remaining_attempts = 3 - password_reset_codes[email]['attempts']

        if remaining_attempts > 0:
            return False, f'Invalid verification code. {remaining_attempts} attempts remaining.'
        else:
            del password_reset_codes[email]
            return False, 'Too many failed attempts. Please request a new verification code.'

def cleanup_verification_code(email):
    """Remove verification code after successful use"""
    if email in password_reset_codes:
        del password_reset_codes[email]

def is_verification_valid(email):
    """Check if there's a valid verification session for the email"""
    return email in password_reset_codes
