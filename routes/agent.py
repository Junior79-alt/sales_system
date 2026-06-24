from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import get_current_user
from datetime import datetime, timedelta

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
# ADMIN: DELETE AGENT DATA (UPDATED - WITH CAPITAL RECALCULATION)
# ============================================
@router.delete("/delete/{data_id}")
def delete_agent_data(
    data_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Hakikisha ni Admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete agent data!"
        )
    
    # Tafuta data ya agent
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.id == data_id
    ).first()
    
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent data not found!"
        )
    
    # Hifadhi staff_id kabla ya kufuta
    staff_id = agent_data.staff_id
    
    # Futa data
    db.delete(agent_data)
    db.commit()
    
    # ===== HESABU UPYA MTAJI NA FAIDA =====
    # Pata data zote zilizobaki za staff huyu
    remaining_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id
    ).order_by(models.AgentData.date.asc()).all()
    
    # Pata capital ya staff
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    if capital and remaining_data:
        # Hesabu jumla ya cash na float zote
        total_cash = sum(d.cash for d in remaining_data)
        total_float = sum(d.float_voda + d.float_airtel + d.float_tigo for d in remaining_data)
        total_spent = total_cash + total_float
        
        # Sasisha current_capital
        capital.current_capital = total_spent
        
        # Hesabu faida upya
        # Faida = Jumla ya matumizi yote - Mtaji wa mwanzo
        capital.total_profit = total_spent - capital.initial_capital
        
        db.commit()
        db.refresh(capital)
    elif capital and not remaining_data:
        # Kama hakuna data iliyobaki, rudisha mtaji kwa initial
        capital.current_capital = capital.initial_capital
        capital.total_profit = 0
        db.commit()
        db.refresh(capital)
    
    return {
        "message": f"✅ Agent data ID {data_id} deleted successfully!",
        "deleted_id": data_id
    }


# ============================================
# ADMIN: DELETE ALL AGENT DATA FOR A STAFF (UPDATED)
# ============================================
@router.delete("/delete_by_staff/{staff_id}")
def delete_agent_data_by_staff(
    staff_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Hakikisha ni Admin
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can delete agent data!"
        )
    
    # Tafuta data zote za staff
    agent_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id
    ).all()
    
    if not agent_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No agent data found for this staff!"
        )
    
    # Hesabu idadi
    count = len(agent_data)
    
    # Futa data zote
    for data in agent_data:
        db.delete(data)
    db.commit()
    
    # ===== RUDISHA MTAJI KWA INITIAL =====
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id
    ).first()
    
    if capital:
        capital.current_capital = capital.initial_capital
        capital.total_profit = 0
        db.commit()
        db.refresh(capital)
    
    return {
        "message": f"✅ {count} agent data records deleted for staff ID {staff_id}!",
        "staff_id": staff_id,
        "deleted_count": count
    }