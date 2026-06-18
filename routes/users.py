from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db
import crud
from auth import verify_password, create_access_token, get_current_user
import models

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBasic()

# ============================================
# REGISTER - Admin anakuwa Active moja kwa moja
# ============================================

@router.post("/register")
def register(name: str, email: str, password: str, role: str = "staff", db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Admin anakuwa active moja kwa moja (is_active = 1)
    # Staff anakuwa inactive (is_active = 0)
    is_active = 1 if role.lower() == "admin" else 0
    
    user = crud.create_user(db, name, email, password, role, is_active=is_active)
    
    if role.lower() == "admin":
        return {
            "message": "Admin created and activated successfully!",
            "user_id": user.id,
            "status": "active"
        }
    else:
        return {
            "message": "Staff registered successfully. Waiting for admin activation.",
            "user_id": user.id,
            "status": "inactive"
        }

# ============================================
# LOGIN - Inaangalia kama user ni active
# ============================================

@router.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, credentials.username)
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not activated. Please contact admin.")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "is_active": user.is_active
    }

# ============================================
# ADMIN: Activate user by email (Bila Token!)
# ============================================

@router.post("/activate_by_email")
def activate_by_email(email: str, db: Session = Depends(get_db)):
    """
    Activate user by email - Hakuna token required!
    Inatumika tu kwenye dashboard ya Admin.
    """
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Admin haja ya ku-activate
    if user.role.lower() == "admin":
        raise HTTPException(status_code=400, detail="Admin already active")
    
    # Ikiwa tayari active
    if user.is_active == 1:
        return {
            "message": f"User {user.name} is already active!",
            "email": user.email,
            "is_active": user.is_active
        }
    
    # Activate user
    user.is_active = 1
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"User {user.name} activated successfully!",
        "email": user.email,
        "is_active": user.is_active
    }

# ============================================
# ADMIN: Get all users (Bila Token!)
# ============================================

@router.get("/all")
def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users - Hakuna token required!
    Inatumika tu kwenye dashboard ya Admin.
    """
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]

# ============================================
# GET CURRENT USER (Inahitaji token)
# ============================================

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }