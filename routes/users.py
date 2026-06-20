from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db
import crud
from auth import verify_password, create_access_token, get_current_user, hash_password
import models
import secrets
import string
import os
import requests
import json

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBasic()

# ============================================
# SENDGRID EMAIL CONFIGURATION
# ============================================
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "wonderfulsirjohn@gmail.com")

def send_email(to_email: str, subject: str, body: str):
    """Tuma barua pepe kwa mtumiaji kutumia SendGrid"""
    if not SENDGRID_API_KEY:
        print("❌ SENDGRID_API_KEY haijapatikana!")
        return False
    
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        html_body = body.replace('\n', '<br>')
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject
                }
            ],
            "from": {"email": SENDGRID_FROM_EMAIL},
            "content": [
                {
                    "type": "text/html",
                    "value": f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; padding: 20px;">
                            <h2 style="color: #1a237e;">📊 Sales System</h2>
                            <hr>
                            <p style="font-size: 16px;">{html_body}</p>
                            <hr>
                            <p style="color: #888; font-size: 12px;">© 2026 Sales System. All rights reserved.</p>
                        </body>
                    </html>
                    """
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 202:
            print(f"✅ Email imetumwa kwa {to_email} via SendGrid")
            return True
        else:
            print(f"❌ SendGrid error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def generate_temporary_password(length: int = 8):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# ============================================
# REGISTER - Inatuma email kwa staff mpya
# ============================================

@router.post("/register")
def register(name: str, email: str, password: str, role: str = "staff", db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    is_active = 1 if role.lower() == "admin" else 0
    user = crud.create_user(db, name, email, password, role, is_active=is_active)
    
    # ===== EMAIL: Staff mpya =====
    if role.lower() == "staff":
        subject = "✅ Akaunti Yako Imewekwa - Sales System"
        body = f"""
Habari {name},

Akaunti yako imeundwa kwenye mfumo wa Sales System.

🔑 Maelezo yako:
   Email: {email}
   Password: {password}

⚠️ Badilisha password yako baada ya kuingia.

Akaunti yako inasubiri ku-ACTIVATE na Admin.

Asante,
Sales System Team
"""
        send_email(email, subject, body)
    
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
# LOGIN
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
# GET CURRENT USER
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

# ============================================
# ADMIN: Get all users
# ============================================

@router.get("/all")
def get_all_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin only."
        )
    
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
# ADMIN: Activate user by email - Inatuma email
# ============================================

@router.post("/activate_by_email")
def activate_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role.lower() == "admin":
        raise HTTPException(status_code=400, detail="Admin already active")
    
    if user.is_active == 1:
        return {
            "message": f"User {user.name} is already active!",
            "email": user.email,
            "is_active": user.is_active
        }
    
    user.is_active = 1
    db.commit()
    db.refresh(user)
    
    # ===== EMAIL: Activation =====
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
Habari {user.name},

Akaunti yako kwenye mfumo wa Sales System ime-ACTIVATED!

🔑 Sasa unaweza kuingia.

Asante,
Sales System Team
"""
    send_email(email, subject, body)
    
    return {
        "message": f"User {user.name} activated successfully!",
        "email": user.email,
        "is_active": user.is_active
    }

# ============================================
# ADMIN: Activate user by ID - Inatuma email
# ============================================

@router.put("/activate/{user_id}")
def activate_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin only."
        )
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate yourself"
        )
    
    if user.role.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin is already active"
        )
    
    user.is_active = 1
    db.commit()
    db.refresh(user)
    
    # ===== EMAIL: Activation =====
    subject = "✅ Akaunti Yako IME-ACTIVATED - Sales System"
    body = f"""
Habari {user.name},

Akaunti yako ime-ACTIVATED!

🔑 Sasa unaweza kuingia.

Asante,
Sales System Team
"""
    send_email(user.email, subject, body)
    
    return {
        "message": f"User {user.name} activated successfully!",
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active
    }

# ============================================
# ADMIN: Deactivate user - Inatuma email
# ============================================

@router.put("/deactivate/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin only."
        )
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    if user.role.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate admin"
        )
    
    user.is_active = 0
    db.commit()
    db.refresh(user)
    
    # ===== EMAIL: Deactivation =====
    subject = "⛔ Akaunti Yako IME-DEACTIVATED - Sales System"
    body = f"""
Habari {user.name},

Akaunti yako ime-DEACTIVATED.

Huwezi kuingia mpaka Admin aku-activate.

Asante,
Sales System Team
"""
    send_email(user.email, subject, body)
    
    return {
        "message": f"User {user.name} deactivated successfully!",
        "user_id": user.id,
        "email": user.email,
        "is_active": user.is_active
    }

# ============================================
# ADMIN: Delete user
# ============================================

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin only."
        )
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    if user.role.lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin"
        )
    
    db.delete(user)
    db.commit()
    
    return {
        "message": f"User {user.name} deleted successfully!",
        "user_id": user.id,
        "email": user.email
    }

# ============================================
# FORGOT PASSWORD - Inatuma email
# ============================================

@router.post("/forgot_password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email haijapatikana!"
        )
    
    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akaunti yako haija-active."
        )
    
    temp_password = generate_temporary_password(8)
    hashed_temp = hash_password(temp_password)
    user.password = hashed_temp
    db.commit()
    
    # ===== EMAIL: Password ya kianzio =====
    subject = "🔑 Password ya Kianzio - Sales System"
    body = f"""
Habari {user.name},

Umeomba kuweka upya password yako.

🔑 Password yako ya kianzio ni: {temp_password}

Ingia kwa password hii, kisha ubadilishe password yako.

Asante,
Sales System Team
"""
    
    send_email(email, subject, body)
    
    return {
        "message": "✅ Password ya kianzio imetumwa!",
        "email": email,
        "temp_password": temp_password
    }

# ============================================
# RESET PASSWORD - Inatuma email
# ============================================

@router.post("/reset_password")
def reset_password(
    email: str,
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )
    
    if not verify_password(old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password ya kianzio si sahihi!"
        )
    
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password mpya iwe na angalau herufi 6!"
        )
    
    user.password = hash_password(new_password)
    db.commit()
    
    # ===== EMAIL: Password imebadilishwa =====
    subject = "✅ Password Yako Imebadilishwa - Sales System"
    body = f"""
Habari {user.name},

Password yako imebadilishwa kwa mafanikio!

🔑 Password mpya: {new_password}

Asante,
Sales System Team
"""
    send_email(user.email, subject, body)
    
    return {
        "message": "✅ Password yako imebadilishwa!",
        "email": user.email
    }