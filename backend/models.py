"""
SQLAlchemy-модели для системы управления продажами автомобилей.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Buyer(Base):
    """Покупатель."""

    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)  # ФИО
    phone = Column(String(20), nullable=True)  # телефон
    email = Column(String(100), nullable=True)  # email

    # Связь: один покупатель — много автомобилей (проданных ему)
    cars = relationship("Car", back_populates="buyer")


class Car(Base):
    """Автомобиль."""

    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), unique=True, nullable=False)  # VIN-код
    model = Column(String(100), nullable=False)  # модель автомобиля
    color = Column(String(50), nullable=False)  # цвет
    purchase_price = Column(Float, nullable=False)  # цена закупки
    sale_price = Column(Float, nullable=True)  # цена продажи
    status = Column(String(20), default="на складе", nullable=False)  # на складе, продан, в демозале, на сервисе
    location = Column(String(100), default="склад", nullable=False)  # текущее местоположение
    arrival_date = Column(DateTime, nullable=False)  # дата поступления
    sale_date = Column(DateTime, nullable=True)  # дата продажи
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=True)

    # Связи
    buyer = relationship("Buyer", back_populates="cars")
    movements = relationship("Movement", back_populates="car", order_by="Movement.date")
    operations = relationship("Operation", back_populates="car")


class Movement(Base):
    """Перемещение автомобиля."""

    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    from_location = Column(String(100), nullable=False)
    to_location = Column(String(100), nullable=False)

    car = relationship("Car", back_populates="movements")


class Operation(Base):
    """Операция / лог (поступление, перемещение, продажа)."""

    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=True)
    operation_type = Column(String(50), nullable=False)  # поступление, перемещение, продажа
    date = Column(DateTime, nullable=False)
    details = Column(Text, nullable=True)  # детали операции
    user = Column(String(100), default="system", nullable=False)

    car = relationship("Car", back_populates="operations")
