"""
CRUD-операции для системы управления продажами автомобилей.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend import models
from backend import schemas


# --- Автомобили ---

def create_car(db: Session, car: schemas.CarCreate) -> models.Car:
    """Создать новый автомобиль и запись в Operation с типом «поступление»."""
    db_car = models.Car(
        vin=car.vin,
        model=car.model,
        color=car.color,
        purchase_price=car.purchase_price,
        arrival_date=car.arrival_date,
        status="на складе",
        location="склад",
    )
    db.add(db_car)
    db.commit()
    db.refresh(db_car)

    # Лог операции «поступление»
    db_operation = models.Operation(
        car_id=db_car.id,
        operation_type="поступление",
        date=datetime.utcnow(),
        details=f"Поступление автомобиля VIN {db_car.vin}, {db_car.model}",
        user="system",
    )
    db.add(db_operation)
    db.commit()

    return db_car


def get_car(db: Session, car_id: int) -> models.Car | None:
    """Получить автомобиль по ID."""
    return db.query(models.Car).filter(models.Car.id == car_id).first()


def get_car_by_vin(db: Session, vin: str) -> models.Car | None:
    """Получить автомобиль по VIN."""
    return db.query(models.Car).filter(models.Car.vin == vin).first()


def get_cars(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[models.Car]:
    """Получить список автомобилей с пагинацией и опциональным фильтром по статусу."""
    q = db.query(models.Car)
    if status is not None:
        q = q.filter(models.Car.status == status)
    return q.offset(skip).limit(limit).all()


def get_cars_in_stock(db: Session) -> List[models.Car]:
    """Получить только автомобили со статусом «на складе»."""
    return db.query(models.Car).filter(models.Car.status == "на складе").all()


def update_car(
    db: Session, car_id: int, car_update: schemas.CarUpdate
) -> models.Car | None:
    """Обновить данные автомобиля (только переданные поля)."""
    db_car = get_car(db, car_id)
    if not db_car:
        return None

    update_data = car_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_car, field, value)

    db.commit()
    db.refresh(db_car)
    return db_car


def delete_car(db: Session, car_id: int) -> bool:
    """Удалить автомобиль (жёсткое удаление: сначала связанные операции и перемещения)."""
    db_car = get_car(db, car_id)
    if not db_car:
        return False

    # Удалить связанные записи (Operation, Movement)
    db.query(models.Operation).filter(models.Operation.car_id == car_id).delete()
    db.query(models.Movement).filter(models.Movement.car_id == car_id).delete()
    db.delete(db_car)
    db.commit()
    return True


# --- Перемещения ---

def _status_by_location(to_location: str) -> str:
    """Статус автомобиля в зависимости от местоположения."""
    mapping = {
        "склад": "на складе",
        "демозал": "в демозале",
        "сервис": "на сервисе",
    }
    return mapping.get(to_location.lower().strip(), "на складе")


def move_car(
    db: Session,
    vin: str,
    from_location: str,
    to_location: str,
    date: datetime,
) -> models.Movement | None:
    """
    Переместить автомобиль по VIN: создать Movement, обновить location и status,
    записать операцию «перемещение».
    """
    db_car = get_car_by_vin(db, vin)
    if not db_car:
        return None

    # Проверка текущего местоположения (пропуск, если from_location пустой)
    if from_location and db_car.location != from_location:
        return None

    # Запись перемещения
    db_movement = models.Movement(
        car_id=db_car.id,
        date=date,
        from_location=db_car.location,
        to_location=to_location,
    )
    db.add(db_movement)
    db.flush()

    # Обновить автомобиль
    db_car.location = to_location
    db_car.status = _status_by_location(to_location)

    # Лог операции «перемещение»
    db_operation = models.Operation(
        car_id=db_car.id,
        operation_type="перемещение",
        date=date,
        details=f"Перемещение VIN {vin}: {db_movement.from_location} -> {to_location}",
        user="system",
    )
    db.add(db_operation)
    db.commit()
    db.refresh(db_movement)
    return db_movement


def get_car_movements(db: Session, car_id: int) -> List[models.Movement]:
    """Получить историю перемещений автомобиля."""
    return (
        db.query(models.Movement)
        .filter(models.Movement.car_id == car_id)
        .order_by(models.Movement.date)
        .all()
    )


def get_all_movements(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Movement]:
    """Получить все перемещения с пагинацией."""
    return (
        db.query(models.Movement)
        .order_by(models.Movement.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# --- Покупатели ---

def create_buyer(db: Session, buyer: schemas.BuyerCreate) -> models.Buyer:
    """Создать нового покупателя."""
    db_buyer = models.Buyer(
        name=buyer.name,
        phone=buyer.phone,
        email=buyer.email,
    )
    db.add(db_buyer)
    db.commit()
    db.refresh(db_buyer)
    return db_buyer


def get_buyer_by_name(db: Session, name: str) -> models.Buyer | None:
    """Найти покупателя по имени (точное совпадение)."""
    return db.query(models.Buyer).filter(models.Buyer.name == name).first()


def get_buyers(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Buyer]:
    """Получить список покупателей с пагинацией."""
    return db.query(models.Buyer).offset(skip).limit(limit).all()


# --- Продажи ---

def sell_car(
    db: Session,
    vin: str,
    sale_price: float,
    buyer_name: str,
    buyer_phone: Optional[str] = None,
    buyer_email: Optional[str] = None,
    sale_date: Optional[datetime] = None,
) -> models.Car | None:
    """
    Продать автомобиль по VIN: создать/найти покупателя, обновить авто,
    записать операцию «продажа».
    """
    db_car = get_car_by_vin(db, vin)
    if not db_car:
        return None
    if db_car.status == "продан":
        return None

    # Создать или найти покупателя по имени
    db_buyer = get_buyer_by_name(db, buyer_name)
    if not db_buyer:
        db_buyer = create_buyer(
            db,
            schemas.BuyerCreate(
                name=buyer_name,
                phone=buyer_phone,
                email=buyer_email,
            ),
        )

    # Обновить автомобиль
    db_car.status = "продан"
    db_car.sale_price = sale_price
    db_car.sale_date = sale_date if sale_date is not None else datetime.utcnow()
    db_car.buyer_id = db_buyer.id

    # Лог операции «продажа»
    db_operation = models.Operation(
        car_id=db_car.id,
        operation_type="продажа",
        date=db_car.sale_date,
        details=f"Продажа VIN {vin} покупателю {buyer_name}, цена {sale_price}",
        user="system",
    )
    db.add(db_operation)
    db.commit()
    db.refresh(db_car)
    return db_car


def get_sold_cars(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[models.Car]:
    """Получить проданные автомобили, при необходимости отфильтровать по периоду (sale_date)."""
    q = db.query(models.Car).filter(models.Car.status == "продан")
    if start_date is not None:
        q = q.filter(models.Car.sale_date >= start_date)
    if end_date is not None:
        q = q.filter(models.Car.sale_date <= end_date)
    return q.order_by(models.Car.sale_date.desc()).all()


# --- Операции (журнал) ---

def get_operations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    operation_type: Optional[str] = None,
) -> List[models.Operation]:
    """Получить журнал операций с пагинацией и опциональным фильтром по типу."""
    q = db.query(models.Operation).order_by(models.Operation.date.desc())
    if operation_type is not None:
        q = q.filter(models.Operation.operation_type == operation_type)
    return q.offset(skip).limit(limit).all()
