from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models

def get_today_sales(db: Session, user_id: int = None):
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    query = db.query(models.Sale).filter(models.Sale.date >= today, models.Sale.date < tomorrow)
    
    if user_id:
        query = query.filter(models.Sale.user_id == user_id)
    
    return query.all()

def calculate_total_amount(sales_list):
    return sum(sale.total_amount for sale in sales_list)

def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d %H:%M:%S")