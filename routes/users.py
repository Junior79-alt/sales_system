from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db
import crud
from auth import verify_password, create_access_token, get_current_user, hash_password
import models
import secrets
import string
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils.email import (
    send_registration_email,
    send_activation_email,
    send_deactivation_email,
    send_forgot_password_email,
    send_reset_password_email,
)
from utils.security import validate_password_strength
from utils.audit import log_action
import pyotp

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBasic()
limiter = Limiter(key_func=get_remote_address)


def generate_temp_password(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


# =========================================================
# REGISTER
# =========================================================
@router.post("/register")
@limiter.limit("10/hour")
def register(
    request: Request,
    name: str,
    email: str,
    password: str,
    staff_type: str = "shop",
    db: Session = Depends(get_db),
):
    if staff_type not in ("shop", "agent"):
        raise HTTPException(status_code=400, detail="staff_type must be 'shop' or 'agent'")

    # ✅ Password strength
    validate_password_strength(password)

    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = crud.create_user(db, name, email, password, role="staff", is_active=0, staff_type=staff_type)
    send_registration_email(email, name, staff_type)
    log_action(db, user.id, "register", f"New {staff_type}: {email}", request)

    return {
        "message": f"Registered as {staff_type}. Waiting for admin activation.",
        "user_id": user.id,
        "status": "inactive",
        "staff_type": staff_type,
    }


# =========================================================
# LOGIN
# =========================================================
@router.post("/login")
@limiter.limit("5/minute")  # ✅ Brute force protection
def login(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, credentials.username)
    if not user or not verify_password(credentials.password, user.password):
        log_action(db, None, "login_failed", f"Failed login: {credentials.username}", request)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not activated. Contact admin.")

    # ✅ 2FA check
    if user.totp_enabled:
        return JSONResponse({
            "requires_2fa": True,
            "user_id": user.id,
            "message": "2FA code required",
        })

    token = create_access_token({"user_id": user.id, "role": user.role})
    log_action(db, user.id, "login", f"Login: {user.email}", request)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "staff_type": user.staff_type,
        "is_active": user.is_active,
    }


# =========================================================
# 2FA
# =========================================================
@router.post("/2fa/setup")
def setup_2fa(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.totp_enabled:
        raise HTTPException(400, "2FA already enabled")

    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email, issuer_name="Sales System"
    )

    current_user.totp_secret = secret
    db.commit()

    return {
        "secret": secret,
        "qr_uri": uri,
        "message": "Scan QR code with Google Authenticator",
    }


@router.post("/2fa/verify")
def verify_2fa(
    code: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(400, "2FA not set up")

    if not pyotp.TOTP(current_user.totp_secret).verify(code):
        raise HTTPException(400, "Invalid 2FA code")

    current_user.totp_enabled = True
    db.commit()
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
def disable_2fa(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    return {"message": "2FA disabled"}


# =========================================================
# GET CURRENT USER
# =========================================================
@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "staff_type": current_user.staff_type,
        "is_active": current_user.is_active,
        "totp_enabled": current_user.totp_enabled,
    }


# =========================================================
# GET ALL USERS (Admin)
# =========================================================
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


# =========================================================
# ACTIVATE USER
# =========================================================
@router.post("/activate_by_email")
def activate_by_email(
    request: Request,
    email: str,
    current_user: models.User = Depends(get_current_user),
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
    log_action(db, current_user.id, "activate_user", f"Activated: {email}", request)

    return {
        "message": f"User {user.name} activated successfully",
        "email": user.email,
        "staff_type": user.staff_type,
        "is_active": user.is_active,
    }


# =========================================================
# DEACTIVATE USER
# =========================================================
@router.put("/deactivate/{user_id}")
def deactivate_user(
    request: Request,
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
    send_deactivation_email(user.email, user.name)
    log_action(db, current_user.id, "deactivate_user", f"Deactivated: {user.email}", request)
    return {"message": f"User {user.name} deactivated"}


# =========================================================
# DELETE USER
# =========================================================
@router.delete("/{user_id}")
def delete_user(
    request: Request,
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

    email = user.email
    db.delete(user)
    db.commit()
    log_action(db, current_user.id, "delete_user", f"Deleted: {email}", request)
    return {"message": f"User {user.name} deleted"}


# =========================================================
# FORGOT PASSWORD — Tuma password ya kianzio kwa email
# =========================================================
@router.post("/forgot_password")
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    email: str,
    db: Session = Depends(get_db),
):
    """
    ✅ Tuma password ya kianzio kwa email.
    Kama email haipo, rudisha ujumbe ule ule (no enumeration).
    """
    user = crud.get_user_by_email(db, email)
    if user and user.is_active == 1:
        temp_password = generate_temp_password(8)
        user.password = hash_password(temp_password)
        db.commit()
        send_forgot_password_email(user.email, user.name, temp_password)
        log_action(db, user.id, "forgot_password", f"Password reset: {email}", request)

    return {"message": "Kama email ipo kwenye system, password ya kianzio imetumwa."}


# =========================================================
# RESET PASSWORD — Badilisha password kwa kutumia password ya kianzio
# =========================================================
@router.post("/reset_password")
def reset_password(
    request: Request,
    email: str,
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    """
    ✅ Badilisha password kwa kutumia password ya kianzio.
    - Inathibitisha password ya kianzio ni sahihi
    - Inathibitisha password mpya ina nguvu
    - Inabadilisha password
    - Inatuma email ya uthibitisho
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=401, detail="Old password incorrect")

    # ✅ Validate new password strength
    validate_password_strength(new_password)

    # ✅ Prevent same password
    if old_password == new_password:
        raise HTTPException(status_code=400, detail="New password must be different from old")

    user.password = hash_password(new_password)
    db.commit()
    send_reset_password_email(user.email, user.name)
    log_action(db, user.id, "reset_password", f"Password changed: {email}", request)

    return {"message": "✅ Password yako imebadilishwa!", "email": user.email}