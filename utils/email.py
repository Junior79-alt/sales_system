import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import Config

# ============================================
# SEND EMAIL VIA SMTP (GMAIL)
# ============================================

def send_email(to_email, subject, body, plain_body=None):
    """
    Tuma barua pepe kwa mtumiaji kutumia SMTP (Gmail)
    Hii inaboresha deliverability na kuepusha spam
    """
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print("⚠️ SMTP credentials not configured! Email not sent.")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body[:200]}...")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = Config.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Plain text body
        if plain_body is None:
            plain_body = body
        
        # HTML body
        html_body = body.replace('\n', '<br>')
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; background-color: #f9f9f9; padding: 20px; margin: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
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
        
        # Attach both plain text and HTML
        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {to_email} via SMTP")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


# ============================================
# EMAIL FUNCTIONS
# ============================================

def send_registration_email(email, name, password, staff_type):
    """Email ya Registration"""
    subject = "✅ Akaunti Yako Imewekwa - Sales System"
    plain_body = f"""Habari {name},

Akaunti yako imeundwa kwenye Sales System.

Maelezo yako:
   Email: {email}
   Password: {password}
   Aina: {staff_type.upper()}

Badilisha password yako baada ya kuingia.

Akaunti yako inasubiri ku-ACTIVATE na Admin.

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Akaunti yako imeundwa kwenye <strong>Sales System</strong>.<br><br>
🔑 <strong>Maelezo yako:</strong><br>
&nbsp;&nbsp;&nbsp;📧 <strong>Email:</strong> {email}<br>
&nbsp;&nbsp;&nbsp;🔑 <strong>Password:</strong> {password}<br>
&nbsp;&nbsp;&nbsp;📌 <strong>Aina:</strong> {staff_type.upper()}<br><br>
⚠️ <strong>Badilisha password yako</strong> baada ya kuingia.<br><br>
Akaunti yako inasubiri ku-<strong>ACTIVATE</strong> na Admin.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_activation_email(email, name, staff_type):
    """Email ya Activation"""
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    plain_body = f"""Habari {name},

Akaunti yako kwenye Sales System ime-ACTIVATED!

Sasa unaweza kuingia.
   Aina: {staff_type.upper()}

Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Akaunti yako kwenye <strong>Sales System</strong> ime-<strong>ACTIVATED</strong>! 🎉<br><br>
🔑 Sasa unaweza kuingia.<br>
&nbsp;&nbsp;&nbsp;📌 <strong>Aina:</strong> {staff_type.upper()}<br><br>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_deactivation_email(email, name):
    """Email ya Deactivation"""
    subject = "⛔ Akaunti Yako IME-DEACTIVATED - Sales System"
    plain_body = f"""Habari {name},

Akaunti yako kwenye Sales System ime-DEACTIVATED.

Huwezi kuingia mpaka Admin aku-activate tena.

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Akaunti yako kwenye <strong>Sales System</strong> ime-<strong>DEACTIVATED</strong>.<br><br>
⛔ Huwezi kuingia mpaka Admin aku-activate tena.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_sale_email(email, name, product_name, quantity, price, total):
    """Email ya Mauzo yamehifadhiwa"""
    subject = "✅ Mauzo Yamehifadhiwa - Sales System"
    plain_body = f"""Habari {name},

Mauzo yako yamehifadhiwa kwa mafanikio!

Maelezo:
   Bidhaa: {product_name}
   Idadi: {quantity}
   Bei: {price:,.0f} TSh
   Jumla: {total:,.0f} TSh

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Mauzo yako yamehifadhiwa kwa mafanikio! 📊<br><br>
📋 <strong>Maelezo:</strong><br>
&nbsp;&nbsp;&nbsp;🏷️ <strong>Bidhaa:</strong> {product_name}<br>
&nbsp;&nbsp;&nbsp;🔢 <strong>Idadi:</strong> {quantity}<br>
&nbsp;&nbsp;&nbsp;💰 <strong>Bei:</strong> {price:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;💵 <strong>Jumla:</strong> {total:,.0f} TSh<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_agent_data_email(email, name, cash, float_voda, float_airtel, float_tigo, total):
    """Email ya Data ya Agent imehifadhiwa"""
    subject = "✅ Data ya Agent Imehifadhiwa - Sales System"
    plain_body = f"""Habari {name},

Data yako ya Agent imehifadhiwa kwa mafanikio!

Maelezo:
   Cash: {cash:,.0f} TSh
   Voda: {float_voda:,.0f} TSh
   Airtel: {float_airtel:,.0f} TSh
   Tigo: {float_tigo:,.0f} TSh
   Jumla: {total:,.0f} TSh

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Data yako ya <strong>Agent</strong> imehifadhiwa kwa mafanikio! 🤖<br><br>
📊 <strong>Maelezo:</strong><br>
&nbsp;&nbsp;&nbsp;💰 <strong>Cash:</strong> {cash:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🟣 <strong>Voda:</strong> {float_voda:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🔴 <strong>Airtel:</strong> {float_airtel:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;🔵 <strong>Tigo:</strong> {float_tigo:,.0f} TSh<br>
&nbsp;&nbsp;&nbsp;📊 <strong>Jumla:</strong> {total:,.0f} TSh<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_forgot_password_email(email, name, temp_password):
    """Email ya Forgot Password"""
    subject = "🔑 Password ya Kianzio - Sales System"
    plain_body = f"""Habari {name},

Umeomba kuweka upya password yako.

Password yako ya kianzio ni: {temp_password}

Ingia hapa: {Config.APP_URL}/dashboard/login.html

Badilisha password yako mara baada ya kuingia.

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Umeomba kuweka upya password yako.<br><br>
🔑 <strong>Password yako ya kianzio ni:</strong><br>
<div style="background: #e8eaf6; padding: 12px; border-radius: 6px; text-align: center; font-size: 20px; font-weight: bold; color: #1a237e; margin: 10px 0;">
    {temp_password}
</div>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
⚠️ <strong>Badilisha password yako</strong> mara baada ya kuingia.<br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)


def send_reset_password_email(email, name):
    """Email ya Reset Password"""
    subject = "✅ Password Yako Imebadilishwa - Sales System"
    plain_body = f"""Habari {name},

Password yako imebadilishwa kwa mafanikio!

Sasa unaweza kuingia kwa password mpya.

Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team"""
    
    body = f"""Habari {name},<br><br>
Password yako imebadilishwa kwa mafanikio! 🔐<br><br>
Sasa unaweza kuingia kwa password mpya.<br><br>
🔗 <a href="{Config.APP_URL}/dashboard/login.html" style="color: #1a237e; text-decoration: none; background: #e8eaf6; padding: 8px 16px; border-radius: 4px;">Ingia hapa</a><br><br>
Asante,<br>
<strong>Sales System Team</strong>"""
    
    return send_email(email, subject, body, plain_body)