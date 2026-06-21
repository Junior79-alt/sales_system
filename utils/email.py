import os
import requests
from datetime import datetime
from config import Config

def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    """
    Tuma barua pepe kwa mtumiaji kutumia SendGrid
    """
    if not Config.is_email_enabled():
        print("⚠️ SendGrid API Key haijapatikana! Email haitatumwa.")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body}")
        return False
    
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        
        if html_body is None:
            html_body = body.replace('\n', '<br>')
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #1a237e, #0d47a1); color: white; padding: 20px; border-radius: 12px 12px 0 0; text-align: center; margin: -30px -30px 20px -30px; }}
                    .header h2 {{ margin: 0; font-size: 24px; }}
                    .content {{ color: #333; line-height: 1.6; }}
                    .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
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
                    </div>
                </div>
            </body>
        </html>
        """
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": Config.SENDGRID_FROM_EMAIL},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {Config.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"📧 Inatuma email kwa {to_email}...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 202:
            print(f"✅ Email imetumwa kwa {to_email} via SendGrid")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        return False

# ===== EMAIL FUNCTIONS =====

def send_registration_email(email: str, name: str, password: str, staff_type: str):
    subject = "✅ Akaunti Yako Imewekwa - Sales System"
    body = f"""
Habari {name},

Akaunti yako imeundwa kwenye mfumo wa {Config.APP_NAME}.

🔑 Maelezo yako:
   📧 Email: {email}
   🔑 Password: {password}
   📌 Aina: {staff_type.upper()}

⚠️ Badilisha password yako baada ya kuingia.

Akaunti yako inasubiri ku-ACTIVATE na Admin.

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_activation_email(email: str, name: str, staff_type: str):
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
Habari {name},

Akaunti yako kwenye mfumo wa {Config.APP_NAME} ime-ACTIVATED! 🎉

🔑 Sasa unaweza kuingia.
   📌 Aina: {staff_type.upper()}

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_deactivation_email(email: str, name: str):
    subject = "⛔ Akaunti Yako IME-DEACTIVATED - Sales System"
    body = f"""
Habari {name},

Akaunti yako kwenye mfumo wa {Config.APP_NAME} ime-DEACTIVATED.

Huwezi kuingia mpaka Admin aku-activate tena.

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_sale_email(email: str, name: str, product_name: str, quantity: int, price: float, total: float):
    subject = "✅ Mauzo Yamehifadhiwa - Sales System"
    body = f"""
Habari {name},

Mauzo yako yamehifadhiwa kwa mafanikio! 📊

📋 Maelezo:
   🏷️ Bidhaa: {product_name}
   🔢 Idadi: {quantity}
   💰 Bei: {price:,.0f} TSh
   💵 Jumla: {total:,.0f} TSh

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_agent_data_email(email: str, name: str, cash: float, float_voda: float, float_airtel: float, float_tigo: float, total: float):
    subject = "✅ Data ya Agent Imehifadhiwa - Sales System"
    body = f"""
Habari {name},

Data yako ya Agent imehifadhiwa kwa mafanikio! 🤖

📊 Maelezo:
   💰 Cash: {cash:,.0f} TSh
   🟣 Voda: {float_voda:,.0f} TSh
   🔴 Airtel: {float_airtel:,.0f} TSh
   🔵 Tigo: {float_tigo:,.0f} TSh
   📊 Jumla: {total:,.0f} TSh

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_forgot_password_email(email: str, name: str, temp_password: str):
    subject = "🔑 Password ya Kianzio - Sales System"
    body = f"""
Habari {name},

Umeomba kuweka upya password yako.

🔑 Password yako ya kianzio ni: {temp_password}

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

⚠️ Badilisha password yako mara baada ya kuingia.

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)

def send_reset_password_email(email: str, name: str):
    subject = "✅ Password Yako Imebadilishwa - Sales System"
    body = f"""
Habari {name},

Password yako imebadilishwa kwa mafanikio! 🔐

Sasa unaweza kuingia kwa password mpya.

🔗 Ingia hapa: {Config.APP_URL}/dashboard/login.html

Asante,
{Config.APP_NAME} Team
"""
    return send_email(email, subject, body)