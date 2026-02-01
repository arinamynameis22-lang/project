# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from database import Base


class Car(Base):
    __tablename__ = "cars"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vin = Column(String(17), unique=True, nullable=False)
    model = Column(String(100), nullable=False)
    color = Column(String(50), nullable=False)
    purchase_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    status = Column(String(20), default="на складе")
    location = Column(String(100), default="склад")
    arrival_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    sale_date = Column(DateTime, nullable=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=True)
    
    # Relationships
    buyer = relationship("Buyer", back_populates="cars")
    movements = relationship("Movement", back_populates="car", cascade="all, delete-orphan")
    operations = relationship("Operation", back_populates="car", cascade="all, delete-orphan")


class Movement(Base):
    __tablename__ = "movements"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    from_location = Column(String(100), nullable=False)
    to_location = Column(String(100), nullable=False)
    
    # Relationships
    car = relationship("Car", back_populates="movements")


class Buyer(Base):
    __tablename__ = "buyers"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Relationships
    cars = relationship("Car", back_populates="buyer")


class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=True)
    operation_type = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    user = Column(String(100), default="system")
    
    # Relationships
    car = relationship("Car", back_populates="operations")
