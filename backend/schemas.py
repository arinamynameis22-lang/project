"""
Pydantic-схемы для валидации данных API.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, model_validator


# --- Car ---

class CarBase(BaseModel):
    """Базовые поля автомобиля."""
    vin: str
    model: str
    color: str
    purchase_price: float


class CarCreate(CarBase):
    """Схема создания автомобиля."""
    arrival_date: datetime


class CarUpdate(BaseModel):
    """Схема обновления автомобиля (все поля опциональны)."""
    vin: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    status: Optional[str] = None
    location: Optional[str] = None
    arrival_date: Optional[datetime] = None
    sale_date: Optional[datetime] = None
    buyer_id: Optional[int] = None


class CarResponse(CarBase):
    """Полная модель автомобиля для ответа."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_price: Optional[float] = None
    status: str
    location: str
    arrival_date: datetime
    sale_date: Optional[datetime] = None
    buyer_id: Optional[int] = None


class CarSale(BaseModel):
    """Схема для продажи автомобиля."""
    sale_price: float
    buyer_name: str
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None


# --- Movement ---

class MovementBase(BaseModel):
    """Базовые поля перемещения (car_id или vin)."""
    car_id: Optional[int] = None
    vin: Optional[str] = None
    from_location: str
    to_location: str
    date: datetime

    @model_validator(mode="after")
    def car_id_or_vin_required(self):
        if self.car_id is None and not self.vin:
            raise ValueError("Необходимо указать car_id или vin")
        return self


class MovementCreate(MovementBase):
    """Схема создания перемещения."""
    pass


class MovementResponse(MovementBase):
    """Схема ответа по перемещению."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: int  # после разрешения по vin будет заполнен


# --- Buyer ---

class BuyerBase(BaseModel):
    """Базовые поля покупателя."""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class BuyerCreate(BuyerBase):
    """Схема создания покупателя."""
    pass


class BuyerResponse(BuyerBase):
    """Схема ответа по покупателю с списком проданных автомобилей."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    cars: List[CarResponse] = []


# --- Operation ---

class OperationResponse(BaseModel):
    """Схема ответа по операции (лог)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: Optional[int] = None
    operation_type: str
    date: datetime
    details: Optional[str] = None
    user: str


# --- Reports ---

class SalesReportItem(BaseModel):
    """Элемент отчёта по продажам (группа model+color)."""
    model: str
    color: str
    count: int
    total_sum: float


class SalesReport(BaseModel):
    """Отчёт по продажам за период."""
    period: str
    total_count: int
    total_sum: float
    items: List[SalesReportItem]


class StockReportItem(BaseModel):
    """Элемент отчёта по остаткам (группа model+color)."""
    model: str
    color: str
    count: int
    cars: List[CarResponse]


class StockReport(BaseModel):
    """Отчёт по остаткам на складе."""
    total_count: int
    items: List[StockReportItem]
