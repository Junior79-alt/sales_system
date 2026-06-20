from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import crud
from auth import get_current_user
import models
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/sales", tags=["Sales"])

# ============================================
# EMAIL CONFIGURATION - GMAIL APP PASSWORD
# ============================================
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "wonderfulsirjohn@gmail.com"
SMTP_PASSWORD = "ysck lojm jrqb stdp"

def send_email(to_email: str, subject: str, body: str):
    """Tuma barua pepe kwa mtumiaji"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email imetumwa kwa {to_email}")
        return True
        
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