from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import crud
from auth import get_current_user
import models
import os
import requests
import json

router = APIRouter(prefix="/sales", tags=["Sales"])

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

# ============================================
# ADD SALE - Inatuma email
# ============================================

@router.post("/")
def add_sale(
    product_name: str,
    quantity: int,
    price: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active."
        )
    
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0"
        )
    
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0"
        )
    
    sale = crud.create_sale(db, product_name, quantity, price, current_user.id)
    
    # ===== EMAIL: Mauzo yamehifadhiwa =====
    subject = "✅ Mauzo Yamehifadhiwa - Sales System"
    body = f"""
Habari {current_user.name},

Mauzo yako yamehifadhiwa kwa mafanikio!

📊 Maelezo:
   🏷️ Bidhaa: {product_name}
   🔢 Idadi: {quantity}
   💰 Bei: {price} TSh
   💵 Jumla: {sale.total_amount} TSh

Asante!
"""
    send_email(current_user.email, subject, body)
    
    return {
        "message": "Sale added successfully",
        "sale_id": sale.id,
        "total_amount": sale.total_amount
    }

# ============================================
# GET ALL SALES
# ============================================

@router.get("/")
def get_sales(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        sales = crud.get_all_sales(db)
    else:
        sales = crud.get_sales_by_user(db, current_user.id)
    
    return sales

# ============================================
# GET SINGLE SALE
# ============================================

@router.get("/{sale_id}")
def get_sale(
    sale_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sale = crud.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    if current_user.role.lower() != "admin" and sale.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return sale

# ============================================
# DELETE SALE
# ============================================

@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sale = crud.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    if current_user.role.lower() != "admin" and sale.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    crud.delete_sale(db, sale_id)
    return {"message": "Sale deleted successfully"}