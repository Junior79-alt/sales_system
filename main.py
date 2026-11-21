from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from database import engine, Base, SessionLocal
from routes import users, sales, agent
import models
from auth import hash_password

print("=" * 50)
print("📝 CHECKING DATABASE TABLES...")
print("=" * 50)
Base.metadata.create_all(bind=engine, checkfirst=True)
print("✅ Tables ready!")


def create_admin():
    """Create admin only ONCE if not exists. Does NOT overwrite password."""
    admin_email = os.environ.get("ADMIN_EMAIL", "").lower().strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not admin_email or not admin_password:
        print("⚠️ ADMIN_EMAIL / ADMIN_PASSWORD not set. Skipping admin creation.")
        return

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.role == "admin").first()
        if existing:
            print(f"✅ Admin exists: {existing.email}")
            return

        admin = models.User(
            name="Admin",
            email=admin_email,
            password=hash_password(admin_password),
            role="admin",
            staff_type="admin",
            is_active=1,
        )
        db.add(admin)
        db.commit()
        print(f"✅ Admin created: {admin_email}")
    finally:
        db.close()


create_admin()


app = FastAPI(
    title="Sales Management System",
    description="API with Agent and Shop Staff System",
    version="3.0.0",
)

# ============ CORS (FIXED: specific origins only) ============
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ ROUTES ============
app.include_router(users.router)
app.include_router(sales.router)
app.include_router(agent.router)

# ============ DASHBOARD ============
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/login.html")


@app.get("/health")
def health():
    return {"status": "OK", "version": "3.0.0"}