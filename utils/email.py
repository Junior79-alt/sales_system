import os
import requests
from datetime import datetime
from config import Config

def send_email(to_email, subject, body):
    """
    Tuma barua pepe kwa SendGrid - PLAIN TEXT VERSION
    Plain text ina deliverability bora kuliko HTML kwa spam filters
    """
    if not Config.SENDGRID_API_KEY:
        print("⚠️ SendGrid API Key haijapatikana!")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        return False
    
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # ===== PLAIN TEXT EMAIL (NO HTML) =====
        # Hii inaonekana halisi na inapita spam filters kwa urahisi
        
        # Add footer to every email
        footer = f"""
---
{Config.APP_NAME}
This is an automated message. Please do not reply to this email.
© {datetime.utcnow().year} {Config.APP_NAME}. All rights reserved.
"""
        
        full_body = body + footer
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {
                "email": Config.SENDGRID_FROM_EMAIL,
                "name": Config.APP_NAME
            },
            "reply_to": {
                "email": Config.SENDGRID_FROM_EMAIL,
                "name": Config.APP_NAME
            },
            "content": [
                {
                    "type": "text/plain",
                    "value": full_body
                }
            ],
            "tracking_settings": {
                "click_tracking": {"enable": False},  # Reduce tracking for better deliverability
                "open_tracking": {"enable": False},
                "subscription_tracking": {"enable": False}
            }
        }
        
        headers = {
            "Authorization": f"Bearer {Config.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"📧 Sending plain text email to {to_email}...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 202:
            print(f"✅ Email sent to {to_email}")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout error sending to {to_email}")
        return False
    except Exception as e:
        print(f"❌ Error sending to {to_email}: {e}")
        return False


# ===== EMAIL FUNCTIONS - PLAIN TEXT VERSION =====

def send_registration_email(email, name, password, staff_type):
    subject = "Akaunti Yako Imewekwa - Sales System"
    body = f"""
Habari {name},

Akaunti yako imeundwa kwenye Sales System.

Maelezo yako:
   Email: {email}
   Password: {password}
   Aina: {staff_type.upper()}

Hatua za kufuata:
   1. Badilisha password yako baada ya kuingia.
   2. Akaunti yako inasubiri ku-ACTIVATE na Admin.
   3. Utapokea email nyingine baada ya ku-ACTIVATE.

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_activation_email(email, name, staff_type):
    subject = "Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
Habari {name},

Akaunti yako kwenye Sales System ime-ACTIVATED!

Sasa unaweza kuingia kwenye mfumo.

Maelezo yako:
   Aina: {staff_type.upper()}
   Login: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_deactivation_email(email, name):
    subject = "Akaunti Yako IME-DEACTIVATED - Sales System"
    body = f"""
Habari {name},

Akaunti yako kwenye Sales System ime-DEACTIVATED.

Huwezi kuingia mpaka Admin aku-activate tena.

Kama una swali, wasiliana na Admin.

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_sale_email(email, name, product_name, quantity, price, total):
    subject = "Mauzo Yamehifadhiwa - Sales System"
    body = f"""
Habari {name},

Mauzo yako yamehifadhiwa kwa mafanikio!

Maelezo:
   Bidhaa: {product_name}
   Idadi: {quantity}
   Bei: {price:,.0f} TSh
   Jumla: {total:,.0f} TSh

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_agent_data_email(email, name, cash, float_voda, float_airtel, float_tigo, total):
    subject = "Data ya Agent Imehifadhiwa - Sales System"
    body = f"""
Habari {name},

Data yako ya Agent imehifadhiwa kwa mafanikio!

Maelezo:
   Cash: {cash:,.0f} TSh
   Voda: {float_voda:,.0f} TSh
   Airtel: {float_airtel:,.0f} TSh
   Tigo: {float_tigo:,.0f} TSh
   Jumla: {total:,.0f} TSh

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_forgot_password_email(email, name, temp_password):
    subject = "Password ya Kianzio - Sales System"
    body = f"""
Habari {name},

Umeomba kuweka upya password yako.

Password yako ya kianzio ni: {temp_password}

Login: {Config.APP_URL}/dashboard/login.html

Hatua za kufuata:
   1. Ingia kwa password ya kianzio.
   2. Badilisha password yako mara baada ya kuingia.

Asante,
Sales System Team
"""
    return send_email(email, subject, body)


def send_reset_password_email(email, name):
    subject = "Password Yako Imebadilishwa - Sales System"
    body = f"""
Habari {name},

Password yako imebadilishwa kwa mafanikio!

Sasa unaweza kuingia kwa password mpya.

Login: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team
"""
    return send_email(email, subject, body)