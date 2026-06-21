from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import crud
from auth import get_current_user
import models
from utils.email import send_sale_email

router = APIRouter(prefix="/sales", tags=["Sales"])

# ===== ADD SALE =====
@router.post("/")
def add_sale(
    product_name: str,
    quantity: int,
    price: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active.")
    
    if current_user.staff_type != "shop":
        raise HTTPException(status_code=403, detail="Only Shop staff can add sales")
    
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than 0")
    
    sale = crud.create_sale(db, product_name, quantity, price, current_user.id)
    
    # ===== SEND EMAIL: Sale Added =====
    send_sale_email(
        current_user.email,
        current_user.name,
        product_name,
        quantity,
        price,
        sale.total_amount
    )
    
    return {
        "message": "Sale added successfully",
        "sale_id": sale.id,
        "total_amount": sale.total_amount
    }

# ===== GET ALL SALES =====
@router.get("/")
def get_sales(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        sales = crud.get_all_sales(db)
    else:
        sales = crud.get_sales_by_user(db, current_user.id)
    
    return [
        {
            "id": s.id,
            "product_name": s.product_name,
            "quantity": s.quantity,
            "price": s.price,
            "total_amount": s.total_amount,
            "user_id": s.user_id,
            "date": s.date.strftime("%Y-%m-%d %H:%M")
        }
        for s in sales
    ]

# ===== GET SINGLE SALE =====
@router.get("/{sale_id}")
def get_sale(
    sale_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sale = crud.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    if current_user.role.lower() != "admin" and sale.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return sale

# ===== DELETE SALE - ADMIN PEKEE =====
@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete sales!"
        )
    
    sale = crud.get_sale_by_id(db, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    crud.delete_sale(db, sale_id)
    return {"message": "Sale deleted successfully by Admin"}