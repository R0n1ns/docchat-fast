import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_email(
    email_to: str,
    subject_template: str,
    html_template: str,
    environment: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send an email to a recipient.
    """
    # Check if SMTP settings are configured
    if not settings.SMTP_HOST or not settings.SMTP_PORT or not settings.EMAILS_FROM_EMAIL:
        logger.warning("SMTP settings not configured, email not sent")
        # For development, just log the email
        logger.info(f"Would send email to {email_to}: {subject_template}")
        logger.info(f"Content: {html_template}")
        return True
    
    message = MIMEMultipart()
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to
    message["Subject"] = subject_template
    
    message.attach(MIMEText(html_template, "html"))
    
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAILS_FROM_EMAIL, 
                email_to, 
                message.as_string()
            )
        logger.info(f"Email sent to {email_to}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        return False
