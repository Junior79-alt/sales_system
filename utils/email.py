import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime
from config import Config

# ============================================
# SEND EMAIL VIA SENDGRID
# ============================================

def send_email(to_email, subject, body, html_body=None):
    """
    Tuma barua pepe kwa mtumiaji kutumia SendGrid
    """
    # Check if SendGrid is configured
    if not Config.SENDGRID_API_KEY:
        print("⚠️ SendGrid API key not configured! Email not sent.")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        return False
    
    try:
        # Create email message
        from_email = Email(Config.SENDGRID_FROM_EMAIL)
        to_email_obj = To(to_email)
        
        # Prepare HTML content
        if html_body is None:
            html_body = body
        
        # Create full HTML email with template
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px; margin: 0; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
                    .header {{ background: linear-gradient(135deg, #1a237e, #0d47a1); color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; margin: -30px -30px 20px -30px; }}
                    .header h2 {{ margin: 0; font-size: 22px; }}
                    .content {{ padding: 10px 0; line-height: 1.6; font-size: 15px; }}
                    .footer {{ margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>📊 {Config.APP_NAME}</h2>
                    </div>
                    <div class="content">
                        {html_body}
                    </div>
                    <div class="footer">
                        <p>© {datetime.utcnow().year} {Config.APP_NAME}. All rights reserved.</p>
                        <p style="font-size: 11px; color: #aaa;">
                            This email was sent to you because you registered on our platform.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Create SendGrid message
        message = Mail(
            from_email=from_email,
            to_emails=to_email_obj,
            subject=subject,
            html_content=html_content
        )
        
        # Send email
        sg = sendgrid.SendGridAPIClient(Config.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Email sent to {to_email} via SendGrid")
            return True
        else:
            print(f"❌ SendGrid error: Status {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


# ============================================
# EMAIL FUNCTIONS (Zinabaki sawa)
# ============================================

def send_registration_email(email, name, password, staff_type):
    """Email ya Registration"""
    subject = "✅ Akaunti Yako Imewekwa - Sales System"
    body = f"""
Habari {name},<br><br>
Akaunti yako imeundwa kwenye <strong>Sales System</strong>.<br><br>
🔑 <strong>Maelezo yako:</strong><br>
&nbsp;&nbsp;&nbsp;📧 <strong>Email:</strong> {email}<br>
&nbsp;&nbsp;&nbsp;🔑 <strong>Password:</strong> {password}<br>
&nbsp;&nbsp;&nbsp;📌 <strong>Aina:</strong> {staff_type.upper()}<br><br>
⚠️ <strong>Badilisha password yako</strong> baada ya kuingia.<br><br>
Akaunti yako inasubiri ku-<strong>ACTIVATE</strong> na Admin.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_activation_email(email, name, staff_type):
    """Email ya Activation"""
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
Habari {name},<br><br>
Akaunti yako kwenye <strong>Sales System</strong> ime-<strong>ACTIVATED</strong>! 🎉<br><br>
🔑 Sasa unaweza kuingia.<br>
&nbsp;&nbsp;&nbsp;📌 <strong>Aina:</strong> {staff_type.upper()}<br><br>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_deactivation_email(email, name):
    """Email ya Deactivation"""
    subject = "⛔ Akaunti Yako IME-DEACTIVATED - Sales System"
    body = f"""
Habari {name},<br><br>
Akaunti yako kwenye <strong>Sales System</strong> ime-<strong>DEACTIVATED</strong>.<br><br>
⛔ Huwezi kuingia mpaka Admin aku-activate tena.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_sale_email(email, name, product_name, quantity, price, total):
    """Email ya Mauzo yamehifadhiwa"""
    subject = "✅ Mauzo Yamehifadhiwa - Sales System"
    body = f"""
Habari {name},<br><br>
Mauzo yako yamehifadhiwa kwa mafanikio! 📊<br><br>
📋 <strong>Maelezo:</strong><br>
&nbsp;&nbsp;&nbsp;🏷️ <strong>Bidhaa:</strong> {product_name}<br>
&nbsp;&nbsp;&nbsp;🔢 <strong>Idadi:</strong> {quantity}<br>
&nbsp;&nbsp;&nbsp;💰 <strong>Bei:</strong> {price:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;💵 <strong>Jumla:</strong> {total:,.0f} TSh<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_agent_data_email(email, name, cash, float_voda, float_airtel, float_tigo, total):
    """Email ya Data ya Agent imehifadhiwa"""
    subject = "✅ Data ya Agent Imehifadhiwa - Sales System"
    body = f"""
Habari {name},<br><br>
Data yako ya <strong>Agent</strong> imehifadhiwa kwa mafanikio! 🤖<br><br>
📊 <strong>Maelezo:</strong><br>
&nbsp;&nbsp;&nbsp;💰 <strong>Cash:</strong> {cash:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🟣 <strong>Voda:</strong> {float_voda:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🔴 <strong>Airtel:</strong> {float_airtel:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🔵 <strong>Tigo:</strong> {float_tigo:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;📊 <strong>Jumla:</strong> {total:,.0f} TSh<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_forgot_password_email(email, name, temp_password):
    """Email ya Forgot Password"""
    subject = "🔑 Password ya Kianzio - Sales System"
    body = f"""
Habari {name},<br><br>
Umeomba kuweka upya password yako.<br><br>
🔑 <strong>Password yako ya kianzio ni:</strong><br>
<div style="background: #e8eaf6; padding: 12px; border-radius: 6px; text-align: center; font-size: 20px; font-weight: bold; color: #1a237e; margin: 10px 0;">
    {temp_password}
</div>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
⚠️ <strong>Badilisha password yako</strong> mara baada ya kuingia.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_reset_password_email(email, name):
    """Email ya Reset Password"""
    subject = "✅ Password Yako Imebadilishwa - Sales System"
    body = f"""
Habari {name},<br><br>
Password yako imebadilishwa kwa mafanikio! 🔐<br><br>
Sasa unaweza kuingia kwa password mpya.<br><br>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    return send_email(email, subject, body)


def send_invoice_email(to_email, name, invoice_data):
    """Send invoice email to agent"""
    subject = f"📊 Monthly Invoice - {invoice_data['month']} - Sales System"
    
    # Create table rows for daily data
    daily_rows = ""
    for d in invoice_data['daily_data']:
        profit_color = '#2e7d32' if d['daily_profit'] >= 0 else '#d32f2f'
        daily_rows += f"""
        <tr>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:center;">{d['date']}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right;">{d['cash']:,.0f}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; color:#7B1FA2;">{d['float_voda']:,.0f}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; color:#D32F2F;">{d['float_airtel']:,.0f}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; color:#1976D2;">{d['float_tigo']:,.0f}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; font-weight:bold;">{d['daily_total']:,.0f}</td>
            <td style="padding:8px; border-bottom:1px solid #eee; text-align:right; font-weight:bold; color:{profit_color};">{d['daily_profit']:,.0f}</td>
        </tr>
        """
    
    body = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 900px; margin: 0 auto;">
        <h2 style="color: #1a237e; text-align: center; border-bottom: 3px solid #1a237e; padding-bottom: 10px;">
            📊 Sales System - Monthly Invoice
        </h2>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #1a237e;">👤 {invoice_data['staff_name']}</h3>
            <p style="margin: 5px 0; color: #555;">📧 {invoice_data['staff_email']}</p>
            <p style="margin: 5px 0; color: #555;">📅 Period: <strong>{invoice_data['month']}</strong> | Days Worked: <strong>{invoice_data['days_worked']}</strong></p>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0;">
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #1a237e;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">💰 Total Cash</div>
                <div style="font-size: 18px; font-weight: bold; color: #1a237e; margin-top: 5px;">{invoice_data['total_cash']:,.0f} TSh</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #7B1FA2;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">🟣 Total Voda</div>
                <div style="font-size: 18px; font-weight: bold; color: #7B1FA2; margin-top: 5px;">{invoice_data['total_float_voda']:,.0f} TSh</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #D32F2F;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">🔴 Total Airtel</div>
                <div style="font-size: 18px; font-weight: bold; color: #D32F2F; margin-top: 5px;">{invoice_data['total_float_airtel']:,.0f} TSh</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #1976D2;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">🔵 Total Tigo</div>
                <div style="font-size: 18px; font-weight: bold; color: #1976D2; margin-top: 5px;">{invoice_data['total_float_tigo']:,.0f} TSh</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #e65100;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">💰 Initial Capital</div>
                <div style="font-size: 18px; font-weight: bold; color: #e65100; margin-top: 5px;">{invoice_data['initial_capital']:,.0f} TSh</div>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2e7d32;">
                <div style="font-size: 11px; color: #888; text-transform: uppercase;">📈 Monthly Profit</div>
                <div style="font-size: 18px; font-weight: bold; color: #2e7d32; margin-top: 5px;">{invoice_data['monthly_profit']:,.0f} TSh</div>
            </div>
        </div>
        
        <h4 style="color: #1a237e;">📋 Daily Performance Breakdown</h4>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px;">
            <thead>
                <tr style="background: #1a237e; color: white;">
                    <th style="padding: 8px 12px; text-align: left;">Date</th>
                    <th style="padding: 8px 12px; text-align: right;">Cash</th>
                    <th style="padding: 8px 12px; text-align: right;">Voda</th>
                    <th style="padding: 8px 12px; text-align: right;">Airtel</th>
                    <th style="padding: 8px 12px; text-align: right;">Tigo</th>
                    <th style="padding: 8px 12px; text-align: right;">Total</th>
                    <th style="padding: 8px 12px; text-align: right;">Profit</th>
                </tr>
            </thead>
            <tbody>
                {daily_rows}
                <tr style="background: #e8eaf6; font-weight: bold;">
                    <td style="padding: 8px 12px;"><strong>TOTAL</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['total_cash']:,.0f}</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['total_float_voda']:,.0f}</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['total_float_airtel']:,.0f}</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['total_float_tigo']:,.0f}</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['total_all']:,.0f}</strong></td>
                    <td style="padding: 8px 12px; text-align: right;"><strong>{invoice_data['monthly_profit']:,.0f}</strong></td>
                </tr>
            </tbody>
        </table>
        
        <div style="text-align: center; color: #888; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
            <p>© 2026 Sales System. All rights reserved.</p>
            <p style="font-size: 11px; color: #aaa;">This invoice is generated automatically. Please contact admin for any questions.</p>
        </div>
    </div>
    """
    
    return send_email(to_email, subject, body)