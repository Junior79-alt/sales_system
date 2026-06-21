import os
import requests
from config import Config

def send_email(to_email, subject, body):
    """Tuma barua pepe kwa SendGrid"""
    if not Config.SENDGRID_API_KEY:
        print("⚠️ SendGrid API Key haijapatikana!")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body[:200]}...")
        return False
    
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # Simple email without complex HTML
        html_body = body.replace('\n', '<br>')
        
        data = {
            "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
            "from": {"email": Config.SENDGRID_FROM_EMAIL},
            "content": [{"type": "text/html", "value": f"<h2>📊 Sales System</h2><hr>{html_body}<hr><p style='color:#888;font-size:12px;'>© 2026 Sales System</p>"}]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"📧 Sending email to {to_email}...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 202:
            print(f"✅ Email sent to {to_email}")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# ===== EMAIL FUNCTIONS =====

def send_registration_email(email, name, password, staff_type):
    subject = "✅ Akaunti Yako Imewekwa"
    body = f"""Habari {name},

Akaunti yako imeundwa kwenye Sales System.

🔑 Maelezo yako:
   📧 Email: {email}
   🔑 Password: {password}
   📌 Aina: {staff_type.upper()}

⚠️ Badilisha password yako baada ya kuingia.

Akaunti yako inasubiri ku-ACTIVATE na Admin.

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_activation_email(email, name, staff_type):
    subject = "✅ Akaunti Yako IME-ACTIVATED"
    body = f"""Habari {name},

Akaunti yako kwenye Sales System ime-ACTIVATED! 🎉

🔑 Sasa unaweza kuingia.
   📌 Aina: {staff_type.upper()}

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_deactivation_email(email, name):
    subject = "⛔ Akaunti Yako IME-DEACTIVATED"
    body = f"""Habari {name},

Akaunti yako kwenye Sales System ime-DEACTIVATED.

Huwezi kuingia mpaka Admin aku-activate tena.

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_sale_email(email, name, product_name, quantity, price, total):
    subject = "✅ Mauzo Yamehifadhiwa"
    body = f"""Habari {name},

Mauzo yako yamehifadhiwa kwa mafanikio! 📊

📋 Maelezo:
   🏷️ Bidhaa: {product_name}
   🔢 Idadi: {quantity}
   💰 Bei: {price:,.0f} TSh
   💵 Jumla: {total:,.0f} TSh

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_agent_data_email(email, name, cash, float_voda, float_airtel, float_tigo, total):
    subject = "✅ Data ya Agent Imehifadhiwa"
    body = f"""Habari {name},

Data yako ya Agent imehifadhiwa kwa mafanikio! 🤖

📊 Maelezo:
   💰 Cash: {cash:,.0f} TSh
   🟣 Voda: {float_voda:,.0f} TSh
   🔴 Airtel: {float_airtel:,.0f} TSh
   🔵 Tigo: {float_tigo:,.0f} TSh
   📊 Jumla: {total:,.0f} TSh

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_forgot_password_email(email, name, temp_password):
    subject = "🔑 Password ya Kianzio"
    body = f"""Habari {name},

Umeomba kuweka upya password yako.

🔑 Password yako ya kianzio ni: {temp_password}

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

⚠️ Badilisha password yako mara baada ya kuingia.

Asante,
Sales System Team"""
    return send_email(email, subject, body)

def send_reset_password_email(email, name):
    subject = "✅ Password Yako Imebadilishwa"
    body = f"""Habari {name},

Password yako imebadilishwa kwa mafanikio! 🔐

Sasa unaweza kuingia kwa password mpya.

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
Sales System Team"""
    return send_email(email, subject, body)