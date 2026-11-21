import os
from datetime import datetime, timezone
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To
from config import Config


def _build_html_template(content: str) -> str:
    return f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; background: #f9f9f9; padding: 20px; margin: 0; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #1a237e, #0d47a1); color: #fff; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; margin: -30px -30px 20px -30px; }}
        .content {{ padding: 10px 0; line-height: 1.6; font-size: 15px; }}
        .footer {{ margin-top: 25px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 12px; }}
    </style>
    </head>
    <body>
    <div class="container">
        <div class="header"><h2>📊 {Config.APP_NAME}</h2></div>
        <div class="content">{content}</div>
        <div class="footer">
            <p>© {datetime.now(timezone.utc).year} {Config.APP_NAME}</p>
        </div>
    </div>
    </body>
    </html>
    """


def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
    if not to_email or "@" not in to_email:
        print(f"⚠️ Invalid recipient: {to_email}")
        return False
    if not Config.SENDGRID_API_KEY:
        print(f"⚠️ SendGrid not configured. Skipping email to {to_email}")
        return False

    try:
        html_content = _build_html_template(html_body or body)
        message = Mail(
            from_email=Email(Config.SENDGRID_FROM_EMAIL),
            to_emails=To(to_email),
            subject=subject,
            html_content=html_content,
        )
        sg = sendgrid.SendGridAPIClient(Config.SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code in (200, 202):
            print(f"✅ Email sent to {to_email}")
            return True
        print(f"❌ SendGrid error: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_registration_email(email, name, staff_type):
    subject = "✅ Akaunti Yako Imewekwa - Sales System"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Akaunti yako imeundwa kwenye <strong>{Config.APP_NAME}</strong>.<br><br>
    📧 Email: <strong>{email}</strong><br>
    📌 Aina: <strong>{staff_type.upper()}</strong><br><br>
    ⚠️ Akaunti yako inasubiri ku-activate na Admin. Utapokea email nyingine baada ya ku-activate.<br><br>
    Asante,<br><strong>{Config.APP_NAME} Team</strong>
    """
    return send_email(email, subject, body)


def send_activation_email(email, name, staff_type):
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Akaunti yako ime-<strong>ACTIVATED</strong>! 🎉<br><br>
    📌 Aina: <strong>{staff_type.upper()}</strong><br><br>
    🔗 <a href="{Config.APP_URL}/dashboard/login.html">Ingia hapa</a><br><br>
    Asante,<br><strong>{Config.APP_NAME} Team</strong>
    """
    return send_email(email, subject, body)


def send_deactivation_email(email, name):
    subject = "⛔ Akaunti Yako IME-DEACTIVATED - Sales System"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Akaunti yako ime-<strong>DEACTIVATED</strong>.<br>
    Huwezi kuingia mpaka Admin aku-activate tena.<br><br>
    Asante,<br><strong>{Config.APP_NAME} Team</strong>
    """
    return send_email(email, subject, body)


def send_sale_email(email, name, product_name, quantity, price, total):
    subject = "✅ Mauzo Yamehifadhiwa"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Mauzo yamehifadhiwa!<br><br>
    🏷️ Bidhaa: {product_name}<br>
    🔢 Idadi: {quantity}<br>
    💰 Bei: {price:,.0f} TSh<br>
    💵 Jumla: <strong>{total:,.0f} TSh</strong>
    """
    return send_email(email, subject, body)


def send_forgot_password_email(email, name, temp_password):
    subject = "🔑 Password ya Kianzio"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Password yako ya kianzio ni:<br>
    <div style="background:#e8eaf6; padding:12px; border-radius:6px; text-align:center; font-size:20px; font-weight:bold; color:#1a237e; margin:10px 0;">
        {temp_password}
    </div>
    🔗 <a href="{Config.APP_URL}/dashboard/login.html">Ingia hapa</a><br><br>
    ⚠️ Badilisha password mara baada ya kuingia.
    """
    return send_email(email, subject, body)


def send_reset_password_email(email, name):
    subject = "✅ Password Yako Imebadilishwa"
    body = f"""
    Habari <strong>{name}</strong>,<br><br>
    Password yako imebadilishwa kwa mafanikio!<br><br>
    🔗 <a href="{Config.APP_URL}/dashboard/login.html">Ingia hapa</a>
    """
    return send_email(email, subject, body)


def send_invoice_email(to_email, name, data):
    subject = f"📊 Invoice - {data['month']}"

    daily_rows = ""
    for d in data["daily_data"]:
        color = "#2e7d32" if d["daily_profit"] >= 0 else "#d32f2f"
        daily_rows += f"""
        <tr>
            <td style="padding:6px; border-bottom:1px solid #eee;">{d['date']}</td>
            <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">{d['cash']:,.0f}</td>
            <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">{d['total_float']:,.0f}</td>
            <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">{d['total_lipa']:,.0f}</td>
            <td style="padding:6px; border-bottom:1px solid #eee; text-align:right; font-weight:bold;">{d['daily_total']:,.0f}</td>
            <td style="padding:6px; border-bottom:1px solid #eee; text-align:right; color:{color}; font-weight:bold;">{d['daily_profit']:,.0f}</td>
        </tr>"""

    body = f"""
    <h2 style="color:#1a237e;">📊 Monthly Invoice - {data['month']}</h2>
    <p><strong>👤 {data['staff_name']}</strong> ({data['staff_email']})</p>
    <p>Days worked: <strong>{data['days_worked']}</strong></p>

    <table style="width:100%; margin:15px 0; background:#f8f9fa; padding:15px; border-radius:8px;">
        <tr>
            <td>💰 Total Cash</td><td style="text-align:right;"><strong>{data['total_cash']:,.0f} TSh</strong></td>
        </tr>
        <tr>
            <td>📱 Total Float</td><td style="text-align:right;"><strong>{data['total_float']:,.0f} TSh</strong></td>
        </tr>
        <tr>
            <td>💳 Total Lipa</td><td style="text-align:right;"><strong>{data['total_lipa']:,.0f} TSh</strong></td>
        </tr>
        <tr>
            <td>📊 Grand Total</td><td style="text-align:right;"><strong>{data['total_all']:,.0f} TSh</strong></td>
        </tr>
        <tr>
            <td>💼 Initial Capital</td><td style="text-align:right;"><strong>{data['initial_capital']:,.0f} TSh</strong></td>
        </tr>
        <tr style="background:#e8eaf6;">
            <td><strong>📈 Monthly Profit</strong></td>
            <td style="text-align:right; color:{'#2e7d32' if data['monthly_profit'] >= 0 else '#d32f2f'};">
                <strong>{data['monthly_profit']:,.0f} TSh</strong>
            </td>
        </tr>
    </table>

    <h4>📋 Daily Breakdown</h4>
    <table style="width:100%; border-collapse:collapse; font-size:12px;">
        <thead>
            <tr style="background:#1a237e; color:white;">
                <th style="padding:8px; text-align:left;">Date</th>
                <th style="padding:8px; text-align:right;">Cash</th>
                <th style="padding:8px; text-align:right;">Float</th>
                <th style="padding:8px; text-align:right;">Lipa</th>
                <th style="padding:8px; text-align:right;">Total</th>
                <th style="padding:8px; text-align:right;">Profit</th>
            </tr>
        </thead>
        <tbody>{daily_rows}</tbody>
    </table>
    """
    return send_email(to_email, subject, body)