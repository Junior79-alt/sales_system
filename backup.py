import os
import subprocess
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import glob
import shutil
import gzip
import re
import sys

# ===== CONFIGURATION =====
DATABASE_URL = os.environ.get("DATABASE_URL", "")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_PATH, exist_ok=True)

# Email configuration for alerts
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")

print("=" * 50)
print("🗄️ DATABASE BACKUP SYSTEM")
print("=" * 50)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Database URL: {'✅ Set' if DATABASE_URL else '❌ Not Set'}")
print(f"SMTP: {'✅ Set' if SMTP_USERNAME and SMTP_PASSWORD else '❌ Not Set'}")
print(f"Alert Email: {ALERT_EMAIL if ALERT_EMAIL else '❌ Not Set'}")
print("=" * 50)

def send_alert_email(subject, body, attachment_path=None):
    """Send email alert about backup status"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("⚠️ Email credentials not configured! Skipping alert.")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )
                msg.attach(part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Alert email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to send alert email: {e}")

def backup_postgresql():
    """Backup PostgreSQL database"""
    try:
        # Remove ?sslmode=require if present
        clean_url = DATABASE_URL.split('?')[0]
        
        print(f"📦 Backing up PostgreSQL...")
        print(f"   Using: {clean_url}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_PATH, f"backup_neon_{timestamp}.sql")
        
        print(f"   Backup file: {backup_file}")
        
        # Use pg_dump with clean URL
        cmd = f"pg_dump '{clean_url}' > {backup_file}"
        result = os.system(cmd)
        
        if result == 0 and os.path.exists(backup_file):
            print(f"✅ Backup created successfully!")
            
            # Compress
            compressed_file = backup_file + '.gz'
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            os.remove(backup_file)
            
            file_size = os.path.getsize(compressed_file) / 1024 / 1024
            print(f"✅ Compressed: {os.path.basename(compressed_file)} ({file_size:.2f} MB)")
            
            send_alert_email(
                "✅ Database Backup Successful",
                f"""
Database backup completed successfully!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📄 File: {os.path.basename(compressed_file)}
📊 Size: {file_size:.2f} MB
                """,
                compressed_file
            )
            
            return True
        else:
            print(f"❌ Backup failed! (Exit code: {result})")
            send_alert_email(
                "❌ Database Backup Failed",
                f"""
Database backup failed!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ Error: pg_dump failed with exit code {result}
                """
            )
            return False
            
    except Exception as e:
        print(f"❌ Backup error: {e}")
        send_alert_email(
            "❌ Database Backup Error",
            f"""
Database backup encountered an error!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ Error: {str(e)}
            """
        )
        return False

def backup_sqlite():
    """Backup SQLite database (fallback)"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "db", "sales.db")
        
        if not os.path.exists(db_path):
            print("❌ SQLite database not found!")
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_PATH, f"backup_sqlite_{timestamp}.db")
        
        shutil.copy2(db_path, backup_file)
        
        print(f"✅ SQLite backup created: {backup_file}")
        
        compressed_file = backup_file + '.gz'
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.write(f_in.read())
        
        os.remove(backup_file)
        
        file_size = os.path.getsize(compressed_file) / 1024 / 1024
        
        send_alert_email(
            "✅ SQLite Database Backup Successful",
            f"""
SQLite database backup completed!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📄 File: {os.path.basename(compressed_file)}
📊 Size: {file_size:.2f} MB
            """,
            compressed_file
        )
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite backup error: {e}")
        return False

def list_backups():
    """List all available backups"""
    backups = glob.glob(os.path.join(BACKUP_PATH, "*.sql.gz")) + glob.glob(os.path.join(BACKUP_PATH, "*.db.gz"))
    backups.sort(key=os.path.getmtime, reverse=True)
    
    print("\n📁 AVAILABLE BACKUPS:")
    print("=" * 50)
    if not backups:
        print("No backups found.")
    else:
        for i, backup in enumerate(backups[:10], 1):
            size = os.path.getsize(backup) / 1024 / 1024
            date = datetime.fromtimestamp(os.path.getmtime(backup)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}. {os.path.basename(backup)}")
            print(f"   📅 {date} | 📊 {size:.2f} MB")
    print("=" * 50)
    print(f"Total: {len(backups)} backup(s)")
    print("=" * 50)

def send_invoice_auto():
    """Send automatic invoices to all agents"""
    try:
        print("\n📧 Sending automatic invoices...")
        sys.path.append(os.path.dirname(__file__))
        from routes.agent import send_invoice_auto as send_invoices
        result = send_invoices()
        print(f"✅ {result} invoices sent")
        return result
    except Exception as e:
        print(f"❌ Auto invoice error: {e}")
        return 0

if __name__ == "__main__":
    print("=" * 50)
    print("🗄️ DATABASE BACKUP SYSTEM")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        success = backup_postgresql()
    else:
        success = backup_sqlite()
    
    if success:
        print("✅ Backup completed successfully!")
        list_backups()
        
        print("\n📧 Sending automatic invoices...")
        sent = send_invoice_auto()
        print(f"✅ {sent} invoices sent automatically")
        
        send_alert_email(
            "✅ Backup and Invoice Summary",
            f"""
Backup and Invoice Summary

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ Backup: Success
📧 Invoices: {sent} sent
            """
        )
    else:
        print("❌ Backup failed!")
        send_alert_email(
            "❌ Backup Failed - Check Logs",
            f"""
Backup failed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for details.
            """
        )