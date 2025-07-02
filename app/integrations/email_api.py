"""
Email API Integration for Super Agent.

This module provides integration with email services.
"""

import os
import base64
import json
from typing import Dict, Any, Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailAPI:
    """Integration with email services."""

    def __init__(self, service_type: str = "gmail"):
        """
        Initialize the email API integration.

        Args:
            service_type (str): The email service type. Default is "gmail".
        """
        self.service_type = service_type
        self.smtp_settings = self._get_smtp_settings()
        self.authenticated = False
        self.smtp_server = None

    def _get_smtp_settings(self) -> Dict[str, Any]:
        """
        Get SMTP settings for the email service.

        Returns:
            Dict[str, Any]: The SMTP settings.
        """
        settings = {
            "gmail": {
                "host": "smtp.gmail.com",
                "port": 587,
                "use_tls": True
            },
            "outlook": {
                "host": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True
            },
            "yahoo": {
                "host": "smtp.mail.yahoo.com",
                "port": 587,
                "use_tls": True
            },
            "aol": {
                "host": "smtp.aol.com",
                "port": 587,
                "use_tls": True
            }
        }
        
        return settings.get(self.service_type, settings["gmail"])

    def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with the email service.

        Args:
            email (str): The email address.
            password (str): The password or app password.

        Returns:
            bool: Whether authentication was successful.
        """
        try:
            # Connect to the SMTP server
            self.smtp_server = smtplib.SMTP(
                self.smtp_settings["host"],
                self.smtp_settings["port"]
            )
            
            # Start TLS if required
            if self.smtp_settings["use_tls"]:
                self.smtp_server.starttls()
            
            # Login to the SMTP server
            self.smtp_server.login(email, password)
            
            self.authenticated = True
            return True
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            self.authenticated = False
            return False

    def send_email(self, sender: str, recipient: str, subject: str, body: str, 
                   html_body: Optional[str] = None, cc: Optional[List[str]] = None, 
                   bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            sender (str): The sender email address.
            recipient (str): The recipient email address.
            subject (str): The email subject.
            body (str): The email body (plain text).
            html_body (Optional[str]): The email body (HTML). Default is None.
            cc (Optional[List[str]]): The CC recipients. Default is None.
            bcc (Optional[List[str]]): The BCC recipients. Default is None.

        Returns:
            Dict[str, Any]: The result of the email sending operation.
        """
        if not self.authenticated or not self.smtp_server:
            return {
                "success": False,
                "error": "Not authenticated. Call authenticate() first."
            }
        
        try:
            # Create a multipart message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            
            # Add CC recipients if provided
            if cc:
                msg['Cc'] = ", ".join(cc)
            
            # Add plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Determine all recipients
            all_recipients = [recipient]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            # Send the email
            self.smtp_server.sendmail(sender, all_recipients, msg.as_string())
            
            return {
                "success": True,
                "message": "Email sent successfully."
            }
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def close(self) -> None:
        """Close the SMTP connection."""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
            except Exception:
                pass
            
            self.smtp_server = None
            self.authenticated = False

    def __del__(self) -> None:
        """Destructor to ensure the SMTP connection is closed."""
        self.close()

    def get_draft_instructions(self, sender: str, recipient: str, subject: str, body: str) -> str:
        """
        Get instructions for creating an email draft manually.

        Args:
            sender (str): The sender email address.
            recipient (str): The recipient email address.
            subject (str): The email subject.
            body (str): The email body.

        Returns:
            str: The instructions for creating an email draft manually.
        """
        instructions = f"""
        ## Email Draft Instructions

        I've prepared an email draft for you. Here's how to send it:

        1. Open your email client ({self.service_type.capitalize()})
        2. Create a new email
        3. Set the following details:
           - From: {sender}
           - To: {recipient}
           - Subject: {subject}
        4. Copy and paste the following content into the email body:

        ```
        {body}
        ```

        5. Review the email and make any necessary adjustments
        6. Send the email when ready
        """
        
        return instructions
