from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base, SessionLocal
from routes import users, sales, agent
import models
from auth import hash_password

# Create database tables
Base.metadata.create_all(bind=engine)

# ===== UNDA ADMIN MOJA KWA MOJA =====
def create_default_admin():
    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.email == "Admin3@test.com").first()
        if not admin:
            hashed_pw = hash_password("123")
            admin = models.User(
                name="Admin",
                email="Admin3@test.com",
                password=hashed_pw,
                role="admin",
                staff_type="admin",
                is_active=1
            )
            db.add(admin)
            db.commit()
            print("✅ Admin created successfully!")
            print("   Email: Admin3@test.com")
            print("   Password: 123")
        else:
            print("✅ Admin already exists!")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    finally:
        db.close()

create_default_admin()

app = FastAPI(
    title="Sales Management System",
    description="API with Agent and Shop Staff System",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(users.router)
app.include_router(sales.router)
app.include_router(agent.router)

# Dashboard
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

@app.get("/")
def root():
    return {"message": "Sales System with Agent & Shop Staff", "dashboard": "/dashboard/login.html"}

@app.get("/health")
def health():
    return {"status": "OK"}