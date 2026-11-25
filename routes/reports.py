from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from database import get_db
import models
from auth import get_current_admin
from datetime import datetime, timezone
from collections import defaultdict
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


def utcnow():
    return datetime.now(timezone.utc)


@router.get("/monthly")
def monthly_report(
    year: int = None,
    month: int = None,
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """✅ Ripoti ya mwezi — admin pekee."""
    now = utcnow()
    year = year or now.year
    month = month or now.month

    # Sales
    sales = db.query(models.Sale).filter(
        extract('year', models.Sale.date) == year,
        extract('month', models.Sale.date) == month,
    ).all()

    total_sales = sum(s.total_amount for s in sales)
    total_quantity = sum(s.quantity for s in sales)

    by_product = defaultdict(float)
    for s in sales:
        by_product[s.product_name] += s.total_amount

    by_staff = defaultdict(float)
    for s in sales:
        staff_name = s.user.name if s.user else f"Staff #{s.user_id}"
        by_staff[staff_name] += s.total_amount

    # Agent
    agent_data = db.query(models.AgentData).filter(
        extract('year', models.AgentData.date) == year,
        extract('month', models.AgentData.date) == month,
    ).all()

    agent_total = sum(d.daily_total for d in agent_data)
    agent_profit = sum(d.daily_profit for d in agent_data)

    return {
        "month": f"{year}-{month:02d}",
        "sales": {
            "total_amount": total_sales,
            "total_quantity": total_quantity,
            "count": len(sales),
            "by_product": dict(by_product),
            "by_staff": dict(by_staff),
        },
        "agent": {
            "total": agent_total,
            "profit": agent_profit,
            "days": len(agent_data),
        },
    }


@router.get("/export/sales")
def export_sales_csv(
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """✅ Export sales to CSV — admin pekee."""
    sales = db.query(models.Sale).order_by(models.Sale.date.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Product", "Quantity", "Price", "Total", "Staff", "Date"])

    for s in sales:
        writer.writerow([
            s.id,
            s.product_name,
            s.quantity,
            s.price,
            s.total_amount,
            s.user.name if s.user else "Unknown",
            s.date.strftime("%Y-%m-%d %H:%M"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sales_export.csv"},
    )


@router.get("/audit_log")
def get_audit_log(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """✅ Audit log — admin pekee."""
    logs = db.query(models.AuditLog).order_by(
        models.AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for log in logs
    ]