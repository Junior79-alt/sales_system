from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="staff")
    staff_type = Column(String, default="shop")
    is_active = Column(Integer, default=0)
    totp_secret = Column(String, nullable=True)
    totp_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    sales = relationship("Sale", back_populates="user", cascade="all, delete-orphan")
    agent_data = relationship("AgentData", back_populates="staff", cascade="all, delete-orphan")
    capital = relationship("AgentCapital", back_populates="staff", cascade="all, delete-orphan")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(DateTime, default=utcnow, index=True)

    user = relationship("User", back_populates="sales")


class AgentData(Base):
    __tablename__ = "agent_data"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"), index=True)

    cash = Column(Float, default=0)
    float_halotel = Column(Float, default=0)
    float_voda = Column(Float, default=0)
    float_airtel = Column(Float, default=0)
    float_tigo = Column(Float, default=0)
    lipa_halotel = Column(Float, default=0)
    lipa_voda = Column(Float, default=0)
    lipa_airtel = Column(Float, default=0)
    lipa_tigo = Column(Float, default=0)

    daily_total = Column(Float, default=0)
    daily_profit = Column(Float, default=0)
    date = Column(DateTime, default=utcnow, index=True)
    created_at = Column(DateTime, default=utcnow)

    staff = relationship("User", back_populates="agent_data")


class AgentCapital(Base):
    __tablename__ = "agent_capital"
    __table_args__ = (
        UniqueConstraint("staff_id", "month", name="unique_staff_month"),
    )

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"), index=True)
    initial_capital = Column(Float, default=0)
    current_capital = Column(Float, default=0)
    total_profit = Column(Float, default=0)
    month = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    staff = relationship("User", back_populates="capital")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    details = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=utcnow, index=True)


# ✅ MPYA: Quick Notes kwa Agent
class AgentNote(Base):
    __tablename__ = "agent_notes"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"), index=True)
    note = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    staff = relationship("User", foreign_keys=[staff_id])
    author = relationship("User", foreign_keys=[created_by])