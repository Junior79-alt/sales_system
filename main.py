from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
from database import engine, Base, SessionLocal
from routes import users, sales, agent, reports
import models
from auth import hash_password

print("=" * 50)
print("📝 CHECKING DATABASE TABLES...")
print("=" * 50)
Base.metadata.create_all(bind=engine, checkfirst=True)
print("✅ Tables ready!")

# ============ RATE LIMITER ============
limiter = Limiter(key_func=get_remote_address)


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
    version="4.0.0",
)

# ============ RATE LIMITING ============
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ============ HTTPS ENFORCEMENT ============
# ⚠️ Zima kwa local development (weka ENFORCE_HTTPS=false)
if os.environ.get("ENFORCE_HTTPS", "true").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)


# ============ SECURITY HEADERS ============
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )
    return response


# ============ CORS ============
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
app.include_router(reports.router)  # ✅ MPYA

# ============ DASHBOARD ============
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/login.html")


@app.get("/health")
def health():
    return {"status": "OK", "version": "4.0.0"}


# ============ DEBUG ENDPOINT (ADMIN ONLY) ============
@app.get("/debug/db")
def debug_db():
    # ⚠️ Zima kwenye production (weka DEBUG=false)
    if os.environ.get("DEBUG", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")

    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user"))
        row = result.fetchone()
    return {"database": row[0], "user": row[1]}