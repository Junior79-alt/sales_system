from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db
import crud
from auth import verify_password, create_access_token, get_current_user, hash_password
import models
import secrets
import string
from utils.email import (
    send_registration_email,
    send_activation_email,
    send_deactivation_email,
    send_forgot_password_email,
    send_reset_password_email,
)

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBasic()


def generate_temp_password(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


@router.post("/register")
def register(
    name: str,
    email: str,
    password: str,
    staff_type: str = "shop",
    db: Session = Depends(get_db),
):
    if staff_type not in ("shop", "agent"):
        raise HTTPException(status_code=400, detail="staff_type must be 'shop' or 'agent'")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(db, name, email, password, role="staff", is_active=0, staff_type=staff_type)
    send_registration_email(email, name, staff_type)
    return {
        "message": f"Registered as {staff_type}. Waiting for admin activation.",
        "user_id": user.id,
        "status": "inactive",
        "staff_type": staff_type,
    }


@router.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, credentials.username)
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not activated. Contact admin.")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "staff_type": user.staff_type,
        "is_active": user.is_active,
    }


@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "staff_type": current_user.staff_type,
        "is_active": current_user.is_active,
    }


@router.get("/all")
def get_all_users(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "staff_type": u.staff_type,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in db.query(models.User).all()
    ]


@router.post("/activate_by_email")
def activate_by_email(
    email: str,
    current_user: models.User = Depends(get_current_user),  # ✅ SECURITY FIX
    db: Session = Depends(get_db),
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    user = db.query(models.User).filter(models.User.email == email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role.lower() == "admin":
        raise HTTPException(status_code=400, detail="Admin already active")
    if user.is_active == 1:
        return {"message": f"User {user.name} is already active", "email": user.email}

    user.is_active = 1
    db.commit()
    db.refresh(user)
    send_activation_email(user.email, user.name, user.staff_type)
    return {
        "message": f"User {user.name} activated successfully",
        "email": user.email,
        "staff_type": user.staff_type,
        "is_active": user.is_active,
    }


@router.put("/deactivate/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    if user.role.lower() == "admin":
        raise HTTPException(status_code=400, detail="Cannot deactivate admin")

    user.is_active = 0
    db.commit()
    db.refresh(user)
    send_deactivation_email(user.email, user.name)
    return {"message": f"User {user.name} deactivated"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if user.role.lower() == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.name} deleted"}


@router.post("/forgot_password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    # ✅ SECURITY: always return same message (no email enumeration)
    user = crud.get_user_by_email(db, email)
    if user and user.is_active == 1:
        temp_password = generate_temp_password(8)
        user.password = hash_password(temp_password)
        db.commit()
        send_forgot_password_email(user.email, user.name, temp_password)

    return {"message": "Kama email ipo kwenye system, password ya kianzio imetumwa."}


@router.post("/reset_password")
def reset_password(
    email: str,
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=401, detail="Old password incorrect")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user.password = hash_password(new_password)
    db.commit()
    send_reset_password_email(user.email, user.name)
    return {"message": "Password changed successfully", "email": user.email}