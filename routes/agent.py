from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import get_current_user
from datetime import datetime, timedelta
from utils.email import send_invoice_email

router = APIRouter(prefix="/agent", tags=["Agent"])

# ============================================
# SET CAPITAL (Mtaji wa Mwanzo)
# ============================================
@router.post("/set_capital")
def set_capital(
    capital_amount: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot set capital")
    
    if current_user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only Agent staff can set capital")
    
    existing_capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id
    ).first()
    
    if existing_capital:
        raise HTTPException(
            status_code=400,
            detail=f"Mtaji tayari umewekwa! Mtaji wa mwanzo: {existing_capital.initial_capital:,.0f} TSh"
        )
    
    current_month = datetime.utcnow().strftime("%Y-%m")
    capital = models.AgentCapital(
        staff_id=current_user.id,
        initial_capital=capital_amount,
        current_capital=capital_amount,
        total_profit=0,
        month=current_month
    )
    
    db.add(capital)
    db.commit()
    db.refresh(capital)
    
    return {
        "message": f"✅ Mtaji wa {capital_amount:,.0f} TSh umewekwa kwa mwezi {current_month}!",
        "capital_id": capital.id,
        "initial_capital": capital_amount,
        "current_capital": capital_amount,
        "month": current_month
    }

# ============================================
# GET CAPITAL
# ============================================
@router.get("/get_capital")
def get_capital(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot view capital")
    
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only Agent staff can view capital")
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id
    ).first()
    
    if not capital:
        return {
            "has_capital": False,
            "message": "Hujatoa mtaji. Tafadhali weka mtaji."
        }
    
    return {
        "has_capital": True,
        "capital_id": capital.id,
        "initial_capital": capital.initial_capital,
        "current_capital": capital.current_capital,
        "total_profit": capital.total_profit,
        "month": capital.month
    }

# ============================================
# ADD AGENT DATA
# ============================================
@router.post("/add")
def add_agent_data(
    cash: float,
    float_voda: float,
    float_airtel: float,
    float_tigo: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot add agent data")
    
    if current_user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only Agent staff can add agent data")
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id
    ).first()
    
    if not capital:
        raise HTTPException(
            status_code=400,
            detail="Hujatoa mtaji! Tafadhali weka mtaji kwanza."
        )
    
    daily_total = cash + float_voda + float_airtel + float_tigo
    daily_profit = daily_total - capital.current_capital
    
    agent_data = models.AgentData(
        staff_id=current_user.id,
        cash=cash,
        float_voda=float_voda,
        float_airtel=float_airtel,
        float_tigo=float_tigo,
        daily_total=daily_total,
        daily_profit=daily_profit,
        date=datetime.utcnow()
    )
    
    db.add(agent_data)
    db.commit()
    db.refresh(agent_data)
    
    capital.current_capital = daily_total
    capital.total_profit = capital.total_profit + daily_profit
    
    db.commit()
    db.refresh(capital)
    
    return {
        "message": "✅ Data imehifadhiwa!",
        "id": agent_data.id,
        "cash": cash,
        "float_voda": float_voda,
        "float_airtel": float_airtel,
        "float_tigo": float_tigo,
        "daily_total": daily_total,
        "daily_profit": daily_profit,
        "initial_capital": capital.initial_capital,
        "current_capital": capital.current_capital,
        "total_profit": capital.total_profit
    }

# ============================================
# GET MY DATA
# ============================================
@router.get("/my_data")
def get_my_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot view this")
    
    if current_user.staff_type == "agent":
        capital = db.query(models.AgentCapital).filter(
            models.AgentCapital.staff_id == current_user.id
        ).first()
        
        all_data = db.query(models.AgentData).filter(
            models.AgentData.staff_id == current_user.id
        ).order_by(models.AgentData.date.asc()).all()
        
        total_cash = sum(d.cash for d in all_data)
        total_float_voda = sum(d.float_voda for d in all_data)
        total_float_airtel = sum(d.float_airtel for d in all_data)
        total_float_tigo = sum(d.float_tigo for d in all_data)
        total_float_all = total_float_voda + total_float_airtel + total_float_tigo
        
        initial_capital = capital.initial_capital if capital else 0
        current_capital = capital.current_capital if capital else 0
        total_profit = capital.total_profit if capital else 0
        
        today = datetime.utcnow().date()
        today_data = [d for d in all_data if d.date.date() == today]
        today_total = sum(d.daily_total for d in today_data)
        today_profit = sum(d.daily_profit for d in today_data)
        
        return {
            "staff_id": current_user.id,
            "staff_name": current_user.name,
            "staff_type": current_user.staff_type,
            "has_capital": capital is not None,
            "initial_capital": initial_capital,
            "current_capital": current_capital,
            "total_profit": total_profit,
            "month": capital.month if capital else None,
            "total_cash": total_cash,
            "total_float_voda": total_float_voda,
            "total_float_airtel": total_float_airtel,
            "total_float_tigo": total_float_tigo,
            "total_float_all": total_float_all,
            "today_total": today_total,
            "today_profit": today_profit,
            "history": [
                {
                    "id": d.id,
                    "cash": d.cash,
                    "float_voda": d.float_voda,
                    "float_airtel": d.float_airtel,
                    "float_tigo": d.float_tigo,
                    "total_float": d.float_voda + d.float_airtel + d.float_tigo,
                    "daily_total": d.daily_total,
                    "daily_profit": d.daily_profit,
                    "date": d.date.strftime("%Y-%m-%d %H:%M")
                }
                for d in all_data
            ]
        }
    
    elif current_user.staff_type == "shop":
        sales = db.query(models.Sale).filter(
            models.Sale.user_id == current_user.id
        ).all()
        
        return {
            "staff_id": current_user.id,
            "staff_name": current_user.name,
            "staff_type": current_user.staff_type,
            "total_sales": sum(s.total_amount for s in sales),
            "total_quantity": sum(s.quantity for s in sales),
            "sales_count": len(sales),
            "sales": [
                {
                    "id": s.id,
                    "product_name": s.product_name,
                    "quantity": s.quantity,
                    "price": s.price,
                    "total_amount": s.total_amount,
                    "date": s.date.strftime("%Y-%m-%d %H:%M")
                }
                for s in sales
            ]
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unknown staff type")

# ============================================
# GET ALL AGENT DATA (Admin)
# ============================================
@router.get("/all")
def get_all_agent_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin only.")
    
    data = db.query(models.AgentData).join(models.User).filter(
        models.User.staff_type == "agent"
    ).all()
    
    result = {}
    for item in data:
        staff = db.query(models.User).filter(models.User.id == item.staff_id).first()
        staff_name = staff.name if staff else "Unknown"
        
        if staff_name not in result:
            capital = db.query(models.AgentCapital).filter(
                models.AgentCapital.staff_id == item.staff_id
            ).first()
            
            result[staff_name] = {
                "staff_id": item.staff_id,
                "staff_name": staff_name,
                "staff_type": staff.staff_type if staff else "unknown",
                "initial_capital": capital.initial_capital if capital else 0,
                "current_capital": capital.current_capital if capital else 0,
                "total_profit": capital.total_profit if capital else 0,
                "total_cash": 0,
                "total_float_voda": 0,
                "total_float_airtel": 0,
                "total_float_tigo": 0,
                "total_float_all": 0,
                "history": []
            }
        
        result[staff_name]["total_cash"] += item.cash
        result[staff_name]["total_float_voda"] += item.float_voda
        result[staff_name]["total_float_airtel"] += item.float_airtel
        result[staff_name]["total_float_tigo"] += item.float_tigo
        result[staff_name]["total_float_all"] += (item.float_voda + item.float_airtel + item.float_tigo)
        result[staff_name]["history"].append({
            "id": item.id,
            "cash": item.cash,
            "float_voda": item.float_voda,
            "float_airtel": item.float_airtel,
            "float_tigo": item.float_tigo,
            "total_float": item.float_voda + item.float_airtel + item.float_tigo,
            "daily_total": item.daily_total,
            "daily_profit": item.daily_profit,
            "date": item.date.strftime("%Y-%m-%d %H:%M")
        })
    
    return list(result.values())

# ============================================
# GET SHOP DATA (Admin)
# ============================================
@router.get("/shop_data")
def get_shop_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin only.")
    
    shops = db.query(models.User).filter(
        models.User.staff_type == "shop",
        models.User.is_active == 1
    ).all()
    
    result = []
    for shop in shops:
        sales = db.query(models.Sale).filter(models.Sale.user_id == shop.id).all()
        total_sales = sum(s.total_amount for s in sales)
        total_quantity = sum(s.quantity for s in sales)
        
        result.append({
            "staff_id": shop.id,
            "staff_name": shop.name,
            "staff_type": shop.staff_type,
            "total_sales": total_sales,
            "total_quantity": total_quantity,
            "sales_count": len(sales),
            "sales": [
                {
                    "id": s.id,
                    "product_name": s.product_name,
                    "quantity": s.quantity,
                    "price": s.price,
                    "total_amount": s.total_amount,
                    "date": s.date.strftime("%Y-%m-%d %H:%M")
                }
                for s in sales
            ]
        })
    
    return result

# ============================================
# ADMIN: DELETE AGENT DATA
# ============================================
@router.delete("/delete/{data_id}")
def delete_agent_data(
    data_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete agent data!"
        )
    
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.id == data_id
    ).first()
    
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent data not found!"
        )
    
    staff_id = agent_data.staff_id
    
    db.delete(agent_data)
    db.commit()
    
    remaining_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id
    ).order_by(models.AgentData.date.asc()).all()
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    if capital:
        if remaining_data:
            total_cash = sum(d.cash for d in remaining_data)
            total_float = sum(d.float_voda + d.float_airtel + d.float_tigo for d in remaining_data)
            total_spent = total_cash + total_float
            
            capital.current_capital = total_spent
            capital.total_profit = total_spent - capital.initial_capital
        else:
            capital.current_capital = capital.initial_capital
            capital.total_profit = 0
        
        db.commit()
        db.refresh(capital)
    
    return {
        "message": f"✅ Agent data ID {data_id} deleted successfully!",
        "deleted_id": data_id
    }

# ============================================
# ADMIN: DELETE ALL AGENT DATA FOR A STAFF
# ============================================
@router.delete("/delete_by_staff/{staff_id}")
def delete_agent_data_by_staff(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete agent data!"
        )
    
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id
    ).all()
    
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No agent data found for this staff!"
        )
    
    count = len(agent_data)
    
    for data in agent_data:
        db.delete(data)
    db.commit()
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    if capital:
        db.delete(capital)
        db.commit()
    
    return {
        "message": f"✅ {count} agent data records AND capital deleted for staff ID {staff_id}!",
        "staff_id": staff_id,
        "deleted_count": count
    }

# ============================================
# ADMIN: DELETE INITIAL CAPITAL ONLY
# ============================================
@router.delete("/delete_capital/{staff_id}")
def delete_initial_capital(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete capital!"
        )
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    if not capital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capital not found for this staff!"
        )
    
    staff_name = capital.staff.name if capital.staff else "Unknown"
    initial_capital = capital.initial_capital
    
    db.delete(capital)
    db.commit()
    
    return {
        "message": f"✅ Initial capital of {initial_capital:,.0f} TSh deleted for {staff_name}!",
        "staff_id": staff_id,
        "staff_name": staff_name,
        "deleted_capital": initial_capital
    }


# =========================================================
# INVOICE SYSTEM
# =========================================================

# ===== GET INVOICE DATA FOR AGENT =====
@router.get("/invoice/{staff_id}")
def get_agent_invoice(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can view invoices!"
        )
    
    agent = db.query(models.User).filter(
        models.User.id == staff_id,
        models.User.staff_type == "agent"
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found!")
    
    today = datetime.utcnow().date()
    first_day = today.replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)
    
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id,
        models.AgentData.date >= first_day,
        models.AgentData.date < next_month
    ).order_by(models.AgentData.date.asc()).all()
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    total_cash = sum(d.cash for d in agent_data)
    total_float_voda = sum(d.float_voda for d in agent_data)
    total_float_airtel = sum(d.float_airtel for d in agent_data)
    total_float_tigo = sum(d.float_tigo for d in agent_data)
    total_float = total_float_voda + total_float_airtel + total_float_tigo
    total_all = total_cash + total_float
    
    initial_capital = capital.initial_capital if capital else 0
    monthly_profit = total_all - initial_capital
    
    return {
        "staff_id": agent.id,
        "staff_name": agent.name,
        "staff_email": agent.email,
        "month": today.strftime("%B %Y"),
        "days_worked": len(agent_data),
        "total_cash": total_cash,
        "total_float_voda": total_float_voda,
        "total_float_airtel": total_float_airtel,
        "total_float_tigo": total_float_tigo,
        "total_float": total_float,
        "total_all": total_all,
        "initial_capital": initial_capital,
        "monthly_profit": monthly_profit,
        "has_data": len(agent_data) > 0,
        "daily_data": [
            {
                "date": d.date.strftime("%Y-%m-%d"),
                "cash": d.cash,
                "float_voda": d.float_voda,
                "float_airtel": d.float_airtel,
                "float_tigo": d.float_tigo,
                "total_float": d.float_voda + d.float_airtel + d.float_tigo,
                "daily_total": d.daily_total,
                "daily_profit": d.daily_profit
            }
            for d in agent_data
        ]
    }


# ===== SEND INVOICE TO AGENT (Admin Manual) =====
@router.post("/send_invoice/{staff_id}")
def send_invoice_to_agent(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can send invoice emails!"
        )
    
    agent = db.query(models.User).filter(
        models.User.id == staff_id,
        models.User.staff_type == "agent",
        models.User.is_active == 1
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or not active!")
    
    # Pata invoice data
    today = datetime.utcnow().date()
    first_day = today.replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)
    
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id,
        models.AgentData.date >= first_day,
        models.AgentData.date < next_month
    ).order_by(models.AgentData.date.asc()).all()
    
    if not agent_data:
        raise HTTPException(
            status_code=400,
            detail=f"No data found for {agent.name} this month!"
        )
    
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    total_cash = sum(d.cash for d in agent_data)
    total_float_voda = sum(d.float_voda for d in agent_data)
    total_float_airtel = sum(d.float_airtel for d in agent_data)
    total_float_tigo = sum(d.float_tigo for d in agent_data)
    total_float = total_float_voda + total_float_airtel + total_float_tigo
    total_all = total_cash + total_float
    
    initial_capital = capital.initial_capital if capital else 0
    monthly_profit = total_all - initial_capital
    
    invoice_data = {
        "staff_name": agent.name,
        "staff_email": agent.email,
        "month": today.strftime("%B %Y"),
        "days_worked": len(agent_data),
        "total_cash": total_cash,
        "total_float_voda": total_float_voda,
        "total_float_airtel": total_float_airtel,
        "total_float_tigo": total_float_tigo,
        "total_float": total_float,
        "total_all": total_all,
        "initial_capital": initial_capital,
        "monthly_profit": monthly_profit,
        "daily_data": [
            {
                "date": d.date.strftime("%Y-%m-%d"),
                "cash": d.cash,
                "float_voda": d.float_voda,
                "float_airtel": d.float_airtel,
                "float_tigo": d.float_tigo,
                "total_float": d.float_voda + d.float_airtel + d.float_tigo,
                "daily_total": d.daily_total,
                "daily_profit": d.daily_profit
            }
            for d in agent_data
        ]
    }
    
    # ===== SEND INVOICE EMAIL =====
    send_invoice_email(agent.email, agent.name, invoice_data)
    
    return {
        "message": f"✅ Invoice sent to {agent.email}",
        "agent": agent.name,
        "email": agent.email
    }


# ===== SEND INVOICE TO ALL AGENTS =====
@router.post("/send_invoice_all")
def send_invoice_to_all_agents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can send invoice emails!"
        )
    
    agents = db.query(models.User).filter(
        models.User.staff_type == "agent",
        models.User.is_active == 1
    ).all()
    
    if not agents:
        raise HTTPException(status_code=404, detail="No active agents found!")
    
    sent_count = 0
    failed_count = 0
    errors = []
    
    for agent in agents:
        try:
            today = datetime.utcnow().date()
            first_day = today.replace(day=1)
            next_month = (first_day + timedelta(days=32)).replace(day=1)
            
            agent_data = db.query(models.AgentData).filter(
                models.AgentData.staff_id == agent.id,
                models.AgentData.date >= first_day,
                models.AgentData.date < next_month
            ).order_by(models.AgentData.date.asc()).all()
            
            if not agent_data:
                failed_count += 1
                errors.append(f"{agent.name}: No data this month")
                continue
            
            capital = db.query(models.AgentCapital).filter(
                models.AgentCapital.staff_id == agent.id
            ).first()
            
            total_cash = sum(d.cash for d in agent_data)
            total_float_voda = sum(d.float_voda for d in agent_data)
            total_float_airtel = sum(d.float_airtel for d in agent_data)
            total_float_tigo = sum(d.float_tigo for d in agent_data)
            total_float = total_float_voda + total_float_airtel + total_float_tigo
            total_all = total_cash + total_float
            
            initial_capital = capital.initial_capital if capital else 0
            monthly_profit = total_all - initial_capital
            
            invoice_data = {
                "staff_name": agent.name,
                "staff_email": agent.email,
                "month": today.strftime("%B %Y"),
                "days_worked": len(agent_data),
                "total_cash": total_cash,
                "total_float_voda": total_float_voda,
                "total_float_airtel": total_float_airtel,
                "total_float_tigo": total_float_tigo,
                "total_float": total_float,
                "total_all": total_all,
                "initial_capital": initial_capital,
                "monthly_profit": monthly_profit,
                "daily_data": [
                    {
                        "date": d.date.strftime("%Y-%m-%d"),
                        "cash": d.cash,
                        "float_voda": d.float_voda,
                        "float_airtel": d.float_airtel,
                        "float_tigo": d.float_tigo,
                        "total_float": d.float_voda + d.float_airtel + d.float_tigo,
                        "daily_total": d.daily_total,
                        "daily_profit": d.daily_profit
                    }
                    for d in agent_data
                ]
            }
            
            send_invoice_email(agent.email, agent.name, invoice_data)
            sent_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"{agent.name}: {str(e)}")
    
    return {
        "message": f"✅ Invoice sent to {sent_count} agents",
        "total_agents": len(agents),
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors
    }


# ===== SEND INVOICE AUTO (Called by Cron) =====
def send_invoice_auto():
    """Send invoices to all active agents automatically"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        agents = db.query(models.User).filter(
            models.User.staff_type == "agent",
            models.User.is_active == 1
        ).all()
        
        sent_count = 0
        for agent in agents:
            try:
                today = datetime.utcnow().date()
                first_day = today.replace(day=1)
                next_month = (first_day + timedelta(days=32)).replace(day=1)
                
                agent_data = db.query(models.AgentData).filter(
                    models.AgentData.staff_id == agent.id,
                    models.AgentData.date >= first_day,
                    models.AgentData.date < next_month
                ).order_by(models.AgentData.date.asc()).all()
                
                if not agent_data:
                    continue
                
                capital = db.query(models.AgentCapital).filter(
                    models.AgentCapital.staff_id == agent.id
                ).first()
                
                total_cash = sum(d.cash for d in agent_data)
                total_float_voda = sum(d.float_voda for d in agent_data)
                total_float_airtel = sum(d.float_airtel for d in agent_data)
                total_float_tigo = sum(d.float_tigo for d in agent_data)
                total_float = total_float_voda + total_float_airtel + total_float_tigo
                total_all = total_cash + total_float
                
                initial_capital = capital.initial_capital if capital else 0
                monthly_profit = total_all - initial_capital
                
                invoice_data = {
                    "staff_name": agent.name,
                    "staff_email": agent.email,
                    "month": today.strftime("%B %Y"),
                    "days_worked": len(agent_data),
                    "total_cash": total_cash,
                    "total_float_voda": total_float_voda,
                    "total_float_airtel": total_float_airtel,
                    "total_float_tigo": total_float_tigo,
                    "total_float": total_float,
                    "total_all": total_all,
                    "initial_capital": initial_capital,
                    "monthly_profit": monthly_profit,
                    "daily_data": [
                        {
                            "date": d.date.strftime("%Y-%m-%d"),
                            "cash": d.cash,
                            "float_voda": d.float_voda,
                            "float_airtel": d.float_airtel,
                            "float_tigo": d.float_tigo,
                            "total_float": d.float_voda + d.float_airtel + d.float_tigo,
                            "daily_total": d.daily_total,
                            "daily_profit": d.daily_profit
                        }
                        for d in agent_data
                    ]
                }
                
                send_invoice_email(agent.email, agent.name, invoice_data)
                sent_count += 1
                
            except Exception as e:
                print(f"❌ Failed to send invoice to {agent.email}: {e}")
        
        print(f"✅ Auto invoice sent to {sent_count} agents")
        return sent_count
        
    except Exception as e:
        print(f"❌ Auto invoice error: {e}")
        return 0
    finally:
        db.close()