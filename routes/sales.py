from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import crud
from auth import get_current_user
import models

router = APIRouter(prefix="/sales", tags=["Sales"])

# ============================================
# ADD SALE
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
            detail="Account not active. Please contact admin."
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
    
    return {
        "message": "Sale added successfully",
        "sale_id": sale.id,
        "total_amount": sale.total_amount
    }

# ============================================
# GET ALL SALES (Admin = yote, Staff = yake tu)
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
# GET SALES BY STAFF ID (Admin pekee)
# ============================================

@router.get("/staff/{staff_id}")
def get_sales_by_staff(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pata mauzo ya staff fulani kwa ID yake.
    - Admin pekee ndiye anayeweza kutumia endpoint hii.
    """
    # Hakikisha user ni Admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view sales by staff"
        )
    
    # Hakikisha staff yupo
    staff = crud.get_user_by_id(db, staff_id)
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found"
        )
    
    # Pata mauzo ya staff huyo
    sales = crud.get_sales_by_user(db, staff_id)
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
            detail="Not authorized to view this sale"
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
            detail="Not authorized to delete this sale"
        )
    
    crud.delete_sale(db, sale_id)
    return {"message": "Sale deleted successfully"}