import os
import subprocess
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import glob
import shutil
import gzip
import sys

DATABASE_URL = os.environ.get("DATABASE_URL", "")
BACKUP_PATH = os.path.join(os.path.dirname(__file__), "backups")
os.makedirs(BACKUP_PATH, exist_ok=True)

PG_DUMP = os.environ.get("PGDUMP_PATH", "pg_dump")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")


def send_alert(subject, body, attachment=None):
    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL:
        print("⚠️ SMTP not configured. Skipping alert email.")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = ALERT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if attachment and os.path.exists(attachment):
            with open(attachment, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment)}")
            msg.attach(part)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        print(f"✅ Alert sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"❌ Email error: {e}")


def backup_postgres():
    try:
        clean_url = DATABASE_URL.split("?")[0]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_PATH, f"backup_{timestamp}.sql")

        print(f"📦 Backing up to {backup_file}")
        # ✅ SECURITY: subprocess with list args (no shell injection)
        with open(backup_file, "wb") as f:
            result = subprocess.run(
                [PG_DUMP, "--no-owner", "--no-privileges", "--clean", "--if-exists", clean_url],
                stdout=f, stderr=subprocess.PIPE, text=False,
            )

        if result.returncode != 0 or not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
            print(f"❌ pg_dump failed: {result.stderr.decode()[:500]}")
            send_alert("❌ Backup Failed", f"pg_dump exit {result.returncode}")
            return False

        # Compress
        gz_file = backup_file + ".gz"
        with open(backup_file, "rb") as fin, gzip.open(gz_file, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        os.remove(backup_file)

        size_mb = os.path.getsize(gz_file) / 1024 / 1024
        print(f"✅ Backup OK: {size_mb:.2f} MB")

        send_alert(
            "✅ Backup Successful",
            f"File: {os.path.basename(gz_file)}\nSize: {size_mb:.2f} MB",
            gz_file,
        )
        return True
    except Exception as e:
        print(f"❌ Backup error: {e}")
        send_alert("❌ Backup Error", str(e))
        return False


def backup_sqlite():
    try:
        db_path = os.path.join(os.path.dirname(__file__), "db", "sales.db")
        if not os.path.exists(db_path):
            print("❌ SQLite DB not found")
            return False
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_PATH, f"sqlite_{timestamp}.db")
        shutil.copy2(db_path, backup_file)

        gz_file = backup_file + ".gz"
        with open(backup_file, "rb") as fin, gzip.open(gz_file, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        os.remove(backup_file)

        size_mb = os.path.getsize(gz_file) / 1024 / 1024
        print(f"✅ SQLite backup: {size_mb:.2f} MB")
        send_alert("✅ SQLite Backup", f"Size: {size_mb:.2f} MB", gz_file)
        return True
    except Exception as e:
        print(f"❌ SQLite backup error: {e}")
        return False


def cleanup_old(max_backups=14):
    try:
        files = glob.glob(os.path.join(BACKUP_PATH, "*.gz"))
        files.sort(key=os.path.getmtime, reverse=True)
        for f in files[max_backups:]:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"🗑️ Removed: {os.path.basename(f)}")
            except Exception as e:
                print(f"⚠️ Could not remove {f}: {e}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


def send_invoices():
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from routes.agent import send_invoice_auto
        return send_invoice_auto()
    except Exception as e:
        print(f"⚠️ Auto invoice error: {e}")
        return 0


if __name__ == "__main__":
    print("=" * 50)
    print("🗄️ BACKUP + AUTO INVOICE")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50)

    if DATABASE_URL and "postgres" in DATABASE_URL:
        ok = backup_postgres()
    else:
        print("📦 Using SQLite backup")
        ok = backup_sqlite()

    if ok:
        cleanup_old(14)
        sent = send_invoices()
        send_alert(
            "✅ Daily Summary",
            f"Backup: OK\nInvoices sent: {sent}",
        )
    else:
        print("❌ Backup failed — check logs")