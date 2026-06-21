from sqlalchemy.orm import Session
import models
from auth import hash_password

def create_user(db: Session, name: str, email: str, password: str, role: str = "staff", is_active: int = 0, staff_type: str = "shop"):
    hashed_pw = hash_password(password)
    db_user = models.User(
        name=name,
        email=email,
        password=hashed_pw,
        role=role,
        is_active=is_active,
        staff_type=staff_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(models.User).all()

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
    return user

def activate_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = 1
        db.commit()
        db.refresh(user)
    return user

def deactivate_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if user:
        user.is_active = 0
        db.commit()
        db.refresh(user)
    return user

def create_sale(db: Session, product_name: str, quantity: int, price: float, user_id: int):
    total = quantity * price
    db_sale = models.Sale(
        product_name=product_name,
        quantity=quantity,
        price=price,
        total_amount=total,
        user_id=user_id
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

def get_all_sales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sale).offset(skip).limit(limit).all()

def get_sales_by_user(db: Session, user_id: int):
    return db.query(models.Sale).filter(models.Sale.user_id == user_id).all()

def get_sale_by_id(db: Session, sale_id: int):
    return db.query(models.Sale).filter(models.Sale.id == sale_id).first()

def delete_sale(db: Session, sale_id: int):
    sale = get_sale_by_id(db, sale_id)
    if sale:
        db.delete(sale)
        db.commit()
        return True
    return False