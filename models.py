from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="staff")
    staff_type = Column(String, default="shop")
    is_active = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sales = relationship("Sale", back_populates="user")
    agent_data = relationship("AgentData", back_populates="staff")
    capital = relationship("AgentCapital", back_populates="staff", uselist=False)

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sales")

class AgentData(Base):
    __tablename__ = "agent_data"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"))
    cash = Column(Float, default=0)
    float_voda = Column(Float, default=0)
    float_airtel = Column(Float, default=0)
    float_tigo = Column(Float, default=0)
    daily_total = Column(Float, default=0)
    daily_profit = Column(Float, default=0)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    staff = relationship("User", back_populates="agent_data")

class AgentCapital(Base):
    __tablename__ = "agent_capital"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"), unique=True)
    initial_capital = Column(Float, default=0)
    current_capital = Column(Float, default=0)
    total_profit = Column(Float, default=0)
    month = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    staff = relationship("User", back_populates="capital")