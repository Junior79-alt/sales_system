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
    """Backup PostgreSQL database using multiple methods"""
    try:
        # Remove ?sslmode=require if present
        clean_url = DATABASE_URL.split('?')[0]
        
        print(f"\n📦 Backing up PostgreSQL...")
        print(f"   Using: {clean_url}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_PATH, f"backup_neon_{timestamp}.sql")
        
        print(f"   Backup file: {backup_file}")
        
        # ===== METHOD 1: Try with -v (verbose) flag =====
        print("   🔄 Attempt 1: Using -v (verbose) flag...")
        cmd = f"pg_dump -v --no-owner --no-privileges --clean --if-exists '{clean_url}' > {backup_file}"
        result = os.system(cmd)
        
        # ===== METHOD 2: Try with format custom =====
        if result != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print("   🔄 Attempt 2: Using custom format...")
            backup_file_custom = backup_file.replace('.sql', '.dump')
            cmd = f"pg_dump --no-owner --no-privileges -F c '{clean_url}' -f {backup_file_custom}"
            result = os.system(cmd)
            if result == 0 and os.path.exists(backup_file_custom) and os.path.getsize(backup_file_custom) > 0:
                backup_file = backup_file_custom
        
        # ===== METHOD 3: Try data-only backup =====
        if result != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print("   🔄 Attempt 3: Using data-only backup...")
            backup_file = os.path.join(BACKUP_PATH, f"backup_neon_data_{timestamp}.sql")
            cmd = f"pg_dump --no-owner --no-privileges --data-only '{clean_url}' > {backup_file}"
            result = os.system(cmd)
        
        # ===== METHOD 4: Try with --schema-only =====
        if result != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print("   🔄 Attempt 4: Using schema-only backup...")
            backup_file = os.path.join(BACKUP_PATH, f"backup_neon_schema_{timestamp}.sql")
            cmd = f"pg_dump --no-owner --no-privileges --schema-only '{clean_url}' > {backup_file}"
            result = os.system(cmd)
        
        # ===== METHOD 5: Try with --inserts (for compatibility) =====
        if result != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print("   🔄 Attempt 5: Using --inserts (compatibility mode)...")
            backup_file = os.path.join(BACKUP_PATH, f"backup_neon_inserts_{timestamp}.sql")
            cmd = f"pg_dump --no-owner --no-privileges --inserts '{clean_url}' > {backup_file}"
            result = os.system(cmd)
        
        # ===== METHOD 6: Try with --column-inserts =====
        if result != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print("   🔄 Attempt 6: Using --column-inserts...")
            backup_file = os.path.join(BACKUP_PATH, f"backup_neon_column_inserts_{timestamp}.sql")
            cmd = f"pg_dump --no-owner --no-privileges --column-inserts '{clean_url}' > {backup_file}"
            result = os.system(cmd)
        
        # ===== CHECK IF BACKUP SUCCEEDED =====
        if result == 0 and os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            file_size = os.path.getsize(backup_file) / 1024
            print(f"✅ Backup created successfully! ({file_size:.2f} KB)")
            
            # Compress the backup
            compressed_file = backup_file + '.gz'
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Remove uncompressed file
            os.remove(backup_file)
            
            file_size_mb = os.path.getsize(compressed_file) / 1024 / 1024
            print(f"✅ Compressed: {os.path.basename(compressed_file)} ({file_size_mb:.2f} MB)")
            
            # Send success email
            send_alert_email(
                "✅ Database Backup Successful",
                f"""
Database backup completed successfully!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📄 File: {os.path.basename(compressed_file)}
📊 Size: {file_size_mb:.2f} MB
🗄️ Total Backups: {len(glob.glob(os.path.join(BACKUP_PATH, '*.sql.gz')))} 

The backup is attached to this email.
                """,
                compressed_file
            )
            
            return True
        else:
            print(f"❌ All backup attempts failed! (Exit code: {result})")
            
            # Check if pg_dump exists
            check_cmd = "which pg_dump"
            check_result = os.system(check_cmd)
            if check_result != 0:
                print("   ⚠️ pg_dump not found! PostgreSQL client may not be installed.")
            else:
                print("   ⚠️ pg_dump found but unable to backup. Version mismatch may be the issue.")
            
            send_alert_email(
                "❌ Database Backup Failed",
                f"""
Database backup failed!

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ Error: All backup methods failed with exit code {result}
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
🗄️ Total Backups: {len(glob.glob(os.path.join(BACKUP_PATH, '*.db.gz')))} 

The backup is attached to this email.
            """,
            compressed_file
        )
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite backup error: {e}")
        return False

def list_backups():
    """List all available backups"""
    backups = glob.glob(os.path.join(BACKUP_PATH, "*.sql.gz")) + glob.glob(os.path.join(BACKUP_PATH, "*.db.gz")) + glob.glob(os.path.join(BACKUP_PATH, "*.dump.gz"))
    backups.sort(key=os.path.getmtime, reverse=True)
    
    print("\n📁 AVAILABLE BACKUPS:")
    print("=" * 60)
    if not backups:
        print("No backups found.")
    else:
        total_size = 0
        for i, backup in enumerate(backups[:20], 1):
            size = os.path.getsize(backup) / 1024 / 1024
            total_size += size
            date = datetime.fromtimestamp(os.path.getmtime(backup)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}. {os.path.basename(backup)}")
            print(f"   📅 {date} | 📊 {size:.2f} MB")
        print("-" * 60)
        print(f"📊 Total: {len(backups)} backup(s) | 💾 {total_size:.2f} MB total")
    print("=" * 60)

def send_invoice_auto():
    """Send automatic invoices to all agents"""
    try:
        print("\n📧 Sending automatic invoices...")
        sys.path.append(os.path.dirname(__file__))
        from routes.agent import send_invoice_auto as send_invoices
        result = send_invoices()
        print(f"✅ {result} invoices sent")
        return result
    except ImportError as e:
        print(f"⚠️ Could not import send_invoice_auto: {e}")
        print("   This is normal if running locally without all dependencies.")
        return 0
    except Exception as e:
        print(f"❌ Auto invoice error: {e}")
        return 0

def check_pg_dump_version():
    """Check pg_dump version for debugging"""
    try:
        result = subprocess.run(['pg_dump', '--version'], capture_output=True, text=True)
        print(f"📌 pg_dump version: {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️ Could not check pg_dump version: {e}")
        return None

def cleanup_old_backups(max_backups=30):
    """Keep only the last N backups"""
    try:
        backups = glob.glob(os.path.join(BACKUP_PATH, "*.sql.gz")) + \
                  glob.glob(os.path.join(BACKUP_PATH, "*.db.gz")) + \
                  glob.glob(os.path.join(BACKUP_PATH, "*.dump.gz"))
        backups.sort(key=os.path.getmtime, reverse=True)
        
        if len(backups) > max_backups:
            to_delete = backups[max_backups:]
            for old_file in to_delete:
                os.remove(old_file)
                print(f"🗑️ Removed old backup: {os.path.basename(old_file)}")
            print(f"✅ Cleaned up {len(to_delete)} old backups")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🗄️ DATABASE BACKUP SYSTEM")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Check pg_dump version
    check_pg_dump_version()
    
    # Determine which database to backup
    if DATABASE_URL and "postgresql" in DATABASE_URL:
        success = backup_postgresql()
    else:
        print("📦 Backing up SQLite...")
        success = backup_sqlite()
    
    if success:
        print("\n✅ Backup completed successfully!")
        list_backups()
        
        # Cleanup old backups (keep last 30)
        cleanup_old_backups(30)
        
        # Send automatic invoices
        print("\n📧 Sending automatic invoices...")
        sent = send_invoice_auto()
        print(f"✅ {sent} invoices sent automatically")
        
        # Send final summary
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
        print("\n❌ Backup failed!")
        send_alert_email(
            "❌ Backup Failed - Check Logs",
            f"""
Backup failed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for details.
            """
        )