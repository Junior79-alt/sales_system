import os
import tempfile
from datetime import datetime, timezone
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Attachment, FileContent, FileName, FileType, Disposition
from config import Config
from utils.pdf import generate_invoice_pdf


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


def send_email(to_email: str, subject: str, body: str, html_body: str = None, attachment_path: str = None) -> bool:
    """
    Send email via SendGrid.
    attachment_path: Optional — path to PDF or other file to attach.
    """
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

        # ✅ Ongeza attachment kama ipo
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                data = f.read()
            encoded = __import__("base64").b64encode(data).decode()
            attachment = Attachment(
                FileContent(encoded),
                FileName(os.path.basename(attachment_path)),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
            message.attachment = attachment

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


# ============ EMAILS ZA KAWAIDA ============

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


# ============ INVOICE EMAIL (PDF ATTACHMENT ONLY) ============

def send_invoice_email(to_email, name, data):
    """
    ✅ Tuma invoice kama PDF attachment PEKEE.
    Email body ni ufupi — PDF ina maelezo yote.
    """
    subject = f"📊 Monthly Invoice - {data['month']} - Sales System"

    # ✅ Body FUPI — PDF ina maelezo yote
    body = f"""
    <h2 style="color:#1a237e;">📊 Monthly Invoice — {data['month']}</h2>
    <p>Habari <strong>{name}</strong>,</p>
    <p>Invoice yako ya mwezi <strong>{data['month']}</strong> tafadhari pakuwa kuona taarifa kamili .</p>
    <p style="font-size:13px; color:#666; margin-top:20px;">
        📎 <strong>Attachment:</strong> invoice_{name.replace(' ', '_')}_{data['month'].replace(' ', '_')}.pdf
    </p>
    """

    # Generate PDF kwenye temp file
    tmp_pdf = None
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_pdf = tmp.name
        tmp.close()

        generate_invoice_pdf(data, tmp_pdf)
        print(f"✅ PDF generated: {tmp_pdf}")

        # Tuma email na PDF attachment
        result = send_email(to_email, subject, body, attachment_path=tmp_pdf)
        return result
    except Exception as e:
        print(f"❌ Invoice PDF error: {e}")
        return False
    finally:
        # Futa temp file baada ya kutuma
        if tmp_pdf and os.path.exists(tmp_pdf):
            try:
                os.unlink(tmp_pdf)
            except Exception:
                pass