from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base, SessionLocal
from routes import users, sales, agent
import models
from auth import hash_password, verify_password

# ============================================
# CREATE DATABASE TABLES
# ============================================
Base.metadata.create_all(bind=engine)

# ============================================
# CREATE OR UPDATE DEFAULT ADMIN
# ============================================

def create_or_update_admin():
    db = SessionLocal()
    try:
        # Tafuta Admin yeyote (kwa role)
        admin = db.query(models.User).filter(models.User.role == "admin").first()
        
        if admin:
            # Admin yupo - badilisha credentials
            print("=" * 50)
            print("🔄 Updating existing admin...")
            print(f"   Old Email: {admin.email}")
            
            # Badilisha email na password
            admin.email = "wonderfulsirjohn@gmail.com"
            admin.password = hash_password("Junior79")
            admin.name = "Admin"
            admin.is_active = 1
            
            db.commit()
            db.refresh(admin)
            
            print("✅ Admin updated successfully!")
            print(f"   New Email: {admin.email}")
            print(f"   New Password: Junior79")
            print("=" * 50)
        else:
            # Hakuna Admin - unda mpya
            print("=" * 50)
            print("📝 No admin found. Creating new admin...")
            
            hashed_pw = hash_password("Junior79")
            new_admin = models.User(
                name="Admin",
                email="wonderfulsirjohn@gmail.com",
                password=hashed_pw,
                role="admin",
                staff_type="admin",
                is_active=1
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            
            print("✅ Admin created successfully!")
            print(f"   Email: {new_admin.email}")
            print(f"   Password: Junior79")
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ Error updating/creating admin: {e}")
    finally:
        db.close()

# ============================================
# ANGAZA KAMA KUNA ADMIN WENGI (HIARI)
# ============================================

def check_duplicate_admins():
    db = SessionLocal()
    try:
        admins = db.query(models.User).filter(models.User.role == "admin").all()
        if len(admins) > 1:
            print("⚠️ WARNING: Multiple admins found!")
            for a in admins:
                print(f"   - {a.email} (ID: {a.id})")
            print("   The first admin will be updated.")
        elif len(admins) == 1:
            print(f"✅ Single admin found: {admins[0].email}")
    except Exception as e:
        print(f"⚠️ Could not check admins: {e}")
    finally:
        db.close()

# ============================================
# RUN ADMIN UPDATE
# ============================================

create_or_update_admin()
check_duplicate_admins()

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Sales Management System",
    description="API with Agent and Shop Staff System",
    version="2.0.0"
)

# ============================================
# CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# ROUTES
# ============================================

app.include_router(users.router)
app.include_router(sales.router)
app.include_router(agent.router)

# ============================================
# DASHBOARD (STATIC FILES)
# ============================================

dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {
        "message": "Sales System with Agent & Shop Staff",
        "dashboard": "/dashboard/login.html"
    }

@app.get("/health")
def health():
    return {"status": "OK"}