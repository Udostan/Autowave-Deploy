"""
Invoice Email Service for AutoWave
Sends professional invoice emails to customers after successful payments
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

class InvoiceEmailService:
    """Service for sending invoice emails to customers"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', 'service@autowave.pro')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_email = os.getenv('FROM_EMAIL', 'service@autowave.pro')
        self.from_name = os.getenv('FROM_NAME', 'AutoWave Support')
        
        # Check if email is configured
        self.email_configured = bool(self.smtp_password and self.smtp_password != 'your_email_app_password_here')
        
        if not self.email_configured:
            logger.warning("Email not configured. Invoice emails will be simulated.")
    
    def send_invoice_email(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send invoice email to customer after successful payment"""
        try:
            customer_email = payment_data.get('customer_email')
            if not customer_email:
                return {'success': False, 'error': 'Customer email not provided'}
            
            # Generate invoice content
            invoice_html = self._generate_invoice_html(payment_data)
            invoice_text = self._generate_invoice_text(payment_data)
            
            if not self.email_configured:
                # Simulate email sending
                logger.info(f"Simulated invoice email sent to {customer_email}")
                return {
                    'success': True,
                    'message': 'Invoice email simulated (email not configured)',
                    'recipient': customer_email
                }
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"AutoWave Invoice - {payment_data.get('plan_name', 'Subscription')} Plan"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = customer_email
            
            # Add text and HTML parts
            text_part = MIMEText(invoice_text, 'plain')
            html_part = MIMEText(invoice_html, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Invoice email sent successfully to {customer_email}")
            return {
                'success': True,
                'message': 'Invoice email sent successfully',
                'recipient': customer_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send invoice email: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to send invoice email: {str(e)}'
            }
    
    def _generate_invoice_html(self, payment_data: Dict[str, Any]) -> str:
        """Generate HTML invoice content"""
        
        # Extract payment information
        amount = payment_data.get('amount', 0)
        currency = payment_data.get('currency', 'NGN')
        plan_name = payment_data.get('plan_name', 'Unknown').title()
        billing_cycle = payment_data.get('billing_cycle', 'monthly').title()
        reference = payment_data.get('reference', 'N/A')
        payment_date = payment_data.get('payment_date', datetime.now().strftime('%B %d, %Y'))
        customer_email = payment_data.get('customer_email', '')
        
        # Format amount
        if currency == 'NGN':
            formatted_amount = f"₦{amount:,.2f}"
        else:
            formatted_amount = f"{currency} {amount:,.2f}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AutoWave Invoice</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .logo {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .invoice-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .detail-label {{ font-weight: bold; color: #555; }}
                .detail-value {{ color: #333; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
                .button {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">AutoWave</div>
                    <p>Thank you for your subscription!</p>
                </div>
                
                <div class="content">
                    <h2>Invoice for Your AutoWave Subscription</h2>
                    <p>Dear Valued Customer,</p>
                    <p>Thank you for subscribing to AutoWave! Your payment has been processed successfully. Here are your invoice details:</p>
                    
                    <div class="invoice-details">
                        <div class="detail-row">
                            <span class="detail-label">Invoice Date:</span>
                            <span class="detail-value">{payment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Customer Email:</span>
                            <span class="detail-value">{customer_email}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Plan:</span>
                            <span class="detail-value">{plan_name} Plan</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Billing Cycle:</span>
                            <span class="detail-value">{billing_cycle}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Payment Reference:</span>
                            <span class="detail-value">{reference}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Amount Paid:</span>
                            <span class="detail-value amount">{formatted_amount}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Payment Status:</span>
                            <span class="detail-value" style="color: green; font-weight: bold;">✅ PAID</span>
                        </div>
                    </div>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>Your subscription is now active</li>
                        <li>You have full access to {plan_name} Plan features</li>
                        <li>Your next billing date will be one {billing_cycle.lower()[:-2]} from today</li>
                        <li>You can manage your subscription anytime in your dashboard</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="https://www.botrex.pro" class="button">Access Your Dashboard</a>
                    </div>
                    
                    <p>If you have any questions about your subscription or need support, please don't hesitate to contact us at <a href="mailto:service@autowave.pro">service@autowave.pro</a>.</p>
                    
                    <p>Thank you for choosing AutoWave!</p>
                    
                    <div class="footer">
                        <p><strong>AutoWave</strong><br>
                        Email: service@autowave.pro<br>
                        Website: <a href="https://www.botrex.pro">www.botrex.pro</a></p>
                        
                        <p style="font-size: 12px; color: #999;">
                        This is an automated invoice. Please keep this email for your records.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_invoice_text(self, payment_data: Dict[str, Any]) -> str:
        """Generate plain text invoice content"""
        
        # Extract payment information
        amount = payment_data.get('amount', 0)
        currency = payment_data.get('currency', 'NGN')
        plan_name = payment_data.get('plan_name', 'Unknown').title()
        billing_cycle = payment_data.get('billing_cycle', 'monthly').title()
        reference = payment_data.get('reference', 'N/A')
        payment_date = payment_data.get('payment_date', datetime.now().strftime('%B %d, %Y'))
        customer_email = payment_data.get('customer_email', '')
        
        # Format amount
        if currency == 'NGN':
            formatted_amount = f"₦{amount:,.2f}"
        else:
            formatted_amount = f"{currency} {amount:,.2f}"
        
        text_content = f"""
AutoWave Invoice - Thank You for Your Subscription!

Dear Valued Customer,

Thank you for subscribing to AutoWave! Your payment has been processed successfully.

INVOICE DETAILS:
================
Invoice Date: {payment_date}
Customer Email: {customer_email}
Plan: {plan_name} Plan
Billing Cycle: {billing_cycle}
Payment Reference: {reference}
Amount Paid: {formatted_amount}
Payment Status: ✅ PAID

WHAT'S NEXT:
============
• Your subscription is now active
• You have full access to {plan_name} Plan features
• Your next billing date will be one {billing_cycle.lower()[:-2]} from today
• You can manage your subscription anytime in your dashboard

Access your dashboard: https://www.botrex.pro

SUPPORT:
========
If you have any questions about your subscription or need support, 
please contact us at service@autowave.pro.

Thank you for choosing AutoWave!

---
AutoWave
Email: service@autowave.pro
Website: www.botrex.pro

This is an automated invoice. Please keep this email for your records.
        """
        
        return text_content.strip()

# Global instance
invoice_email_service = InvoiceEmailService()
