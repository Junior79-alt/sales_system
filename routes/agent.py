from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from auth import get_current_user
from datetime import datetime, timedelta, timezone
from utils.email import send_invoice_email

router = APIRouter(prefix="/agent", tags=["Agent"])


def utcnow():
    return datetime.now(timezone.utc)


# ============ CAPITAL ============

@router.post("/set_capital")
def set_capital(
    capital_amount: float,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot set capital")
    if current_user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only agents")
    if capital_amount <= 0:
        raise HTTPException(status_code=400, detail="Capital must be > 0")

    current_month = utcnow().strftime("%Y-%m")
    existing = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id,
        models.AgentCapital.month == current_month,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Capital already set for {current_month}: {existing.initial_capital:,.0f} TSh",
        )

    capital = models.AgentCapital(
        staff_id=current_user.id,
        initial_capital=capital_amount,
        current_capital=capital_amount,
        total_profit=0,
        month=current_month,
    )
    db.add(capital)
    db.commit()
    db.refresh(capital)

    return {
        "message": f"Capital {capital_amount:,.0f} TSh set for {current_month}",
        "capital_id": capital.id,
        "initial_capital": capital_amount,
        "current_capital": capital_amount,
        "month": current_month,
    }


@router.get("/get_capital")
def get_capital(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only agents")

    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id
    ).order_by(models.AgentCapital.id.desc()).first()

    if not capital:
        return {"has_capital": False, "message": "No capital set"}

    return {
        "has_capital": True,
        "capital_id": capital.id,
        "initial_capital": capital.initial_capital,
        "current_capital": capital.current_capital,
        "total_profit": capital.total_profit,
        "month": capital.month,
    }


# ============ AGENT DATA ============

@router.post("/add")
def add_agent_data(
    cash: float = 0,
    float_halotel: float = 0,
    float_voda: float = 0,
    float_airtel: float = 0,
    float_tigo: float = 0,
    lipa_halotel: float = 0,
    lipa_voda: float = 0,
    lipa_airtel: float = 0,
    lipa_tigo: float = 0,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot add agent data")
    if current_user.is_active != 1:
        raise HTTPException(status_code=403, detail="Account not active")
    if current_user.staff_type != "agent":
        raise HTTPException(status_code=403, detail="Only agents")

    current_month = utcnow().strftime("%Y-%m")
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == current_user.id,
        models.AgentCapital.month == current_month,
    ).first()
    if not capital:
        raise HTTPException(status_code=400, detail="Set capital first for this month")

    total_float = float_halotel + float_voda + float_airtel + float_tigo
    total_lipa = lipa_halotel + lipa_voda + lipa_airtel + lipa_tigo
    daily_total = cash + total_float + total_lipa
    daily_profit = daily_total - capital.current_capital  # ✅ Fixed calculation

    agent_data = models.AgentData(
        staff_id=current_user.id,
        cash=cash,
        float_halotel=float_halotel,
        float_voda=float_voda,
        float_airtel=float_airtel,
        float_tigo=float_tigo,
        lipa_halotel=lipa_halotel,
        lipa_voda=lipa_voda,
        lipa_airtel=lipa_airtel,
        lipa_tigo=lipa_tigo,
        daily_total=daily_total,
        daily_profit=daily_profit,
        date=utcnow(),
    )
    db.add(agent_data)
    db.commit()
    db.refresh(agent_data)

    # Update capital — recompute from all data for accuracy
    _recalc_capital(db, capital)

    return {
        "message": "Data saved",
        "id": agent_data.id,
        "daily_total": daily_total,
        "daily_profit": agent_data.daily_profit,
        "initial_capital": capital.initial_capital,
        "current_capital": capital.current_capital,
        "total_profit": capital.total_profit,
    }


def _recalc_capital(db: Session, capital: models.AgentCapital):
    """Recalculate capital based on all agent data for the month"""
    all_data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == capital.staff_id,
        models.AgentData.date >= datetime.strptime(capital.month + "-01", "%Y-%m-%d").replace(tzinfo=timezone.utc),
    ).all()

    if all_data:
        latest = max(all_data, key=lambda x: x.date)
        capital.current_capital = latest.daily_total
    else:
        capital.current_capital = capital.initial_capital

    capital.total_profit = capital.current_capital - capital.initial_capital
    db.commit()


@router.get("/my_data")
def get_my_data(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() == "admin":
        raise HTTPException(status_code=403, detail="Admin cannot view this")

    if current_user.staff_type == "agent":
        current_month = utcnow().strftime("%Y-%m")
        capital = db.query(models.AgentCapital).filter(
            models.AgentCapital.staff_id == current_user.id,
            models.AgentCapital.month == current_month,
        ).first()

        all_data = db.query(models.AgentData).filter(
            models.AgentData.staff_id == current_user.id
        ).order_by(models.AgentData.date.asc()).all()

        total_cash = sum(d.cash for d in all_data)
        total_float_halotel = sum(d.float_halotel for d in all_data)
        total_float_voda = sum(d.float_voda for d in all_data)
        total_float_airtel = sum(d.float_airtel for d in all_data)
        total_float_tigo = sum(d.float_tigo for d in all_data)
        total_float_all = total_float_halotel + total_float_voda + total_float_airtel + total_float_tigo

        total_lipa_halotel = sum(d.lipa_halotel for d in all_data)
        total_lipa_voda = sum(d.lipa_voda for d in all_data)
        total_lipa_airtel = sum(d.lipa_airtel for d in all_data)
        total_lipa_tigo = sum(d.lipa_tigo for d in all_data)
        total_lipa_all = total_lipa_halotel + total_lipa_voda + total_lipa_airtel + total_lipa_tigo

        today = utcnow().date()
        today_data = [d for d in all_data if d.date.date() == today]

        return {
            "staff_id": current_user.id,
            "staff_name": current_user.name,
            "staff_type": current_user.staff_type,
            "has_capital": capital is not None,
            "initial_capital": capital.initial_capital if capital else 0,
            "current_capital": capital.current_capital if capital else 0,
            "total_profit": capital.total_profit if capital else 0,
            "month": capital.month if capital else None,
            "total_cash": total_cash,
            "total_float_halotel": total_float_halotel,
            "total_float_voda": total_float_voda,
            "total_float_airtel": total_float_airtel,
            "total_float_tigo": total_float_tigo,
            "total_float_all": total_float_all,
            "total_lipa_halotel": total_lipa_halotel,
            "total_lipa_voda": total_lipa_voda,
            "total_lipa_airtel": total_lipa_airtel,
            "total_lipa_tigo": total_lipa_tigo,
            "total_lipa_all": total_lipa_all,
            "today_total": sum(d.daily_total for d in today_data),
            "today_profit": sum(d.daily_profit for d in today_data),
            "history": [
                {
                    "id": d.id,
                    "cash": d.cash,
                    "float_halotel": d.float_halotel,
                    "float_voda": d.float_voda,
                    "float_airtel": d.float_airtel,
                    "float_tigo": d.float_tigo,
                    "total_float": d.float_halotel + d.float_voda + d.float_airtel + d.float_tigo,
                    "lipa_halotel": d.lipa_halotel,
                    "lipa_voda": d.lipa_voda,
                    "lipa_airtel": d.lipa_airtel,
                    "lipa_tigo": d.lipa_tigo,
                    "total_lipa": d.lipa_halotel + d.lipa_voda + d.lipa_airtel + d.lipa_tigo,
                    "daily_total": d.daily_total,
                    "daily_profit": d.daily_profit,
                    "date": d.date.strftime("%Y-%m-%d %H:%M"),
                }
                for d in all_data
            ],
        }

    elif current_user.staff_type == "shop":
        sales = db.query(models.Sale).filter(models.Sale.user_id == current_user.id).all()
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
                    "date": s.date.strftime("%Y-%m-%d %H:%M"),
                }
                for s in sales
            ],
        }
    raise HTTPException(status_code=400, detail="Unknown staff type")


@router.get("/all")
def get_all_agent_data(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    data = db.query(models.AgentData).join(models.User).filter(
        models.User.staff_type == "agent"
    ).order_by(models.AgentData.date.asc()).all()

    result = {}
    for item in data:
        staff = db.query(models.User).filter(models.User.id == item.staff_id).first()
        if not staff:
            continue

        key = item.staff_id
        if key not in result:
            current_month = utcnow().strftime("%Y-%m")
            capital = db.query(models.AgentCapital).filter(
                models.AgentCapital.staff_id == item.staff_id,
                models.AgentCapital.month == current_month,
            ).first()
            result[key] = {
                "staff_id": item.staff_id,
                "staff_name": staff.name,
                "staff_type": staff.staff_type,
                "initial_capital": capital.initial_capital if capital else 0,
                "current_capital": capital.current_capital if capital else 0,
                "total_profit": capital.total_profit if capital else 0,
                "total_cash": 0,
                "total_float_halotel": 0,
                "total_float_voda": 0,
                "total_float_airtel": 0,
                "total_float_tigo": 0,
                "total_lipa_halotel": 0,
                "total_lipa_voda": 0,
                "total_lipa_airtel": 0,
                "total_lipa_tigo": 0,
                "history": [],
            }

        result[key]["total_cash"] += item.cash
        result[key]["total_float_halotel"] += item.float_halotel
        result[key]["total_float_voda"] += item.float_voda
        result[key]["total_float_airtel"] += item.float_airtel
        result[key]["total_float_tigo"] += item.float_tigo
        result[key]["total_lipa_halotel"] += item.lipa_halotel
        result[key]["total_lipa_voda"] += item.lipa_voda
        result[key]["total_lipa_airtel"] += item.lipa_airtel
        result[key]["total_lipa_tigo"] += item.lipa_tigo
        result[key]["history"].append({
            "id": item.id,
            "cash": item.cash,
            "float_halotel": item.float_halotel,
            "float_voda": item.float_voda,
            "float_airtel": item.float_airtel,
            "float_tigo": item.float_tigo,
            "total_float": item.float_halotel + item.float_voda + item.float_airtel + item.float_tigo,
            "lipa_halotel": item.lipa_halotel,
            "lipa_voda": item.lipa_voda,
            "lipa_airtel": item.lipa_airtel,
            "lipa_tigo": item.lipa_tigo,
            "total_lipa": item.lipa_halotel + item.lipa_voda + item.lipa_airtel + item.lipa_tigo,
            "daily_total": item.daily_total,
            "daily_profit": item.daily_profit,
            "date": item.date.strftime("%Y-%m-%d %H:%M"),
        })

    return list(result.values())


@router.get("/shop_data")
def get_shop_data(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    shops = db.query(models.User).filter(
        models.User.staff_type == "shop",
        models.User.is_active == 1,
    ).all()

    result = []
    for shop in shops:
        sales = db.query(models.Sale).filter(models.Sale.user_id == shop.id).all()
        result.append({
            "staff_id": shop.id,
            "staff_name": shop.name,
            "staff_type": shop.staff_type,
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
                    "date": s.date.strftime("%Y-%m-%d %H:%M"),
                }
                for s in sales
            ],
        })
    return result


# ============ DELETE (admin) ============

@router.delete("/delete/{data_id}")
def delete_agent_data(data_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    item = db.query(models.AgentData).filter(models.AgentData.id == data_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    staff_id = item.staff_id
    db.delete(item)
    db.commit()

    current_month = utcnow().strftime("%Y-%m")
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id,
        models.AgentCapital.month == current_month,
    ).first()
    if capital:
        _recalc_capital(db, capital)

    return {"message": f"Deleted data ID {data_id}", "deleted_id": data_id}


@router.delete("/delete_by_staff_and_date/{staff_id}")
def delete_agent_data_by_date(
    staff_id: int,
    date: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """✅ NEW: delete all data for a staff on a specific date (single request)"""
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        target = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Date format: YYYY-MM-DD")

    next_day = target + timedelta(days=1)
    entries = db.query(models.AgentData).filter(
        models.AgentData.staff_id == staff_id,
        models.AgentData.date >= target,
        models.AgentData.date < next_day,
    ).all()

    if not entries:
        raise HTTPException(status_code=404, detail="No data for this date")

    count = len(entries)
    for e in entries:
        db.delete(e)
    db.commit()

    current_month = utcnow().strftime("%Y-%m")
    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == staff_id,
        models.AgentCapital.month == current_month,
    ).first()
    if capital:
        _recalc_capital(db, capital)

    return {"message": f"Deleted {count} entries for {date}", "deleted_count": count}


@router.delete("/delete_by_staff/{staff_id}")
def delete_agent_data_by_staff(staff_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    entries = db.query(models.AgentData).filter(models.AgentData.staff_id == staff_id).all()
    if not entries:
        raise HTTPException(status_code=404, detail="No data for this staff")

    count = len(entries)
    for e in entries:
        db.delete(e)
    db.commit()

    capital = db.query(models.AgentCapital).filter(models.AgentCapital.staff_id == staff_id).first()
    if capital:
        db.delete(capital)
        db.commit()

    return {"message": f"Deleted {count} entries + capital for staff {staff_id}", "deleted_count": count}


@router.delete("/delete_capital/{staff_id}")
def delete_capital(staff_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    capital = db.query(models.AgentCapital).filter(models.AgentCapital.staff_id == staff_id).first()
    if not capital:
        raise HTTPException(status_code=404, detail="Capital not found")

    name = capital.staff.name if capital.staff else "Unknown"
    amount = capital.initial_capital
    db.delete(capital)
    db.commit()

    return {"message": f"Capital {amount:,.0f} TSh deleted for {name}", "staff_id": staff_id}


# ============ INVOICE ============

@router.get("/invoice/{staff_id}")
def get_invoice(staff_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    agent = db.query(models.User).filter(models.User.id == staff_id, models.User.staff_type == "agent").first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return _build_invoice(db, agent)


@router.post("/send_invoice/{staff_id}")
def send_invoice(staff_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    agent = db.query(models.User).filter(
        models.User.id == staff_id,
        models.User.staff_type == "agent",
        models.User.is_active == 1,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or inactive")

    data = _build_invoice(db, agent)
    if not data["daily_data"]:
        raise HTTPException(status_code=400, detail=f"No data for {agent.name} this month")

    ok = send_invoice_email(agent.email, agent.name, data)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return {"message": f"Invoice sent to {agent.email}", "agent": agent.name}


@router.post("/send_invoice_all")
def send_invoice_all(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    agents = db.query(models.User).filter(
        models.User.staff_type == "agent",
        models.User.is_active == 1,
    ).all()

    sent, failed, errors = 0, 0, []
    for agent in agents:
        try:
            data = _build_invoice(db, agent)
            if not data["daily_data"]:
                failed += 1
                errors.append(f"{agent.name}: no data")
                continue
            if send_invoice_email(agent.email, agent.name, data):
                sent += 1
            else:
                failed += 1
                errors.append(f"{agent.name}: send failed")
        except Exception as e:
            failed += 1
            errors.append(f"{agent.name}: {e}")

    return {
        "message": f"Invoice sent to {sent}/{len(agents)} agents",
        "total_agents": len(agents),
        "sent": sent,
        "failed": failed,
        "errors": errors,
    }


def send_invoice_auto():
    """Called by cron — returns count of sent invoices"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        agents = db.query(models.User).filter(
            models.User.staff_type == "agent",
            models.User.is_active == 1,
        ).all()
        sent = 0
        for agent in agents:
            try:
                data = _build_invoice(db, agent)
                if data["daily_data"] and send_invoice_email(agent.email, agent.name, data):
                    sent += 1
            except Exception as e:
                print(f"Invoice failed for {agent.email}: {e}")
        return sent
    finally:
        db.close()


def _build_invoice(db: Session, agent: models.User) -> dict:
    today = utcnow().date()
    first_day = today.replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)

    from datetime import timezone as tz
    first_dt = datetime.combine(first_day, datetime.min.time()).replace(tzinfo=tz.utc)
    next_dt = datetime.combine(next_month, datetime.min.time()).replace(tzinfo=tz.utc)

    data = db.query(models.AgentData).filter(
        models.AgentData.staff_id == agent.id,
        models.AgentData.date >= first_dt,
        models.AgentData.date < next_dt,
    ).order_by(models.AgentData.date.asc()).all()

    capital = db.query(models.AgentCapital).filter(
        models.AgentCapital.staff_id == agent.id,
        models.AgentCapital.month == today.strftime("%Y-%m"),
    ).first()

    total_cash = sum(d.cash for d in data)
    total_float = sum(d.float_halotel + d.float_voda + d.float_airtel + d.float_tigo for d in data)
    total_lipa = sum(d.lipa_halotel + d.lipa_voda + d.lipa_airtel + d.lipa_tigo for d in data)
    total_all = total_cash + total_float + total_lipa
    initial = capital.initial_capital if capital else 0

    return {
        "staff_name": agent.name,
        "staff_email": agent.email,
        "month": today.strftime("%B %Y"),
        "days_worked": len(data),
        "total_cash": total_cash,
        "total_float": total_float,
        "total_lipa": total_lipa,
        "total_all": total_all,
        "initial_capital": initial,
        "monthly_profit": total_all - initial,
        "daily_data": [
            {
                "date": d.date.strftime("%Y-%m-%d"),
                "cash": d.cash,
                "total_float": d.float_halotel + d.float_voda + d.float_airtel + d.float_tigo,
                "total_lipa": d.lipa_halotel + d.lipa_voda + d.lipa_airtel + d.lipa_tigo,
                "daily_total": d.daily_total,
                "daily_profit": d.daily_profit,
            }
            for d in data
        ],
    }