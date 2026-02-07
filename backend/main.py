"""
FastAPI приложение: Система управления продажами автомобилей.
"""

import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import crud, file_loader, models, reports, schemas
from backend.database import Base, engine, get_db


# Тела запросов для API (date/sale_date опциональны)
class MovementCreateBody(BaseModel):
    vin: str
    from_location: str
    to_location: str
    date: Optional[datetime] = None


class SaleCreateBody(BaseModel):
    vin: str
    sale_price: float
    buyer_name: str
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    sale_date: Optional[datetime] = None


# Роутеры
cars_router = APIRouter(prefix="/cars", tags=["Автомобили"])
movements_router = APIRouter(prefix="/movements", tags=["Перемещения"])
sales_router = APIRouter(prefix="/sales", tags=["Продажи"])
reports_router = APIRouter(prefix="/reports", tags=["Отчёты"])
files_router = APIRouter(prefix="/files", tags=["Загрузка файлов"])
buyers_router = APIRouter(prefix="/buyers", tags=["Покупатели"])


# --- Эндпоинты: автомобили ---

@cars_router.get("", response_model=list[schemas.CarResponse])
def list_cars(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Получить список автомобилей (пагинация и опциональный фильтр по статусу)."""
    cars = crud.get_cars(db, skip=skip, limit=limit, status=status)
    return cars


@cars_router.get("/stock", response_model=list[schemas.CarResponse])
def list_cars_in_stock(db: Session = Depends(get_db)):
    """Получить автомобили на складе."""
    return crud.get_cars_in_stock(db)


@cars_router.get("/vin/{vin}", response_model=schemas.CarResponse)
def get_car_by_vin(vin: str, db: Session = Depends(get_db)):
    """Получить автомобиль по VIN."""
    car = crud.get_car_by_vin(db, vin)
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return car


@cars_router.get("/{car_id}", response_model=schemas.CarResponse)
def get_car(car_id: int, db: Session = Depends(get_db)):
    """Получить автомобиль по ID."""
    car = crud.get_car(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return car


@cars_router.post("", response_model=schemas.CarResponse, status_code=201)
def create_car(car_in: schemas.CarCreate, db: Session = Depends(get_db)):
    """Создать новый автомобиль."""
    if crud.get_car_by_vin(db, car_in.vin):
        raise HTTPException(status_code=400, detail="Автомобиль с таким VIN уже существует")
    return crud.create_car(db, car_in)


@cars_router.put("/{car_id}", response_model=schemas.CarResponse)
def update_car(car_id: int, car_in: schemas.CarUpdate, db: Session = Depends(get_db)):
    """Обновить автомобиль."""
    car = crud.update_car(db, car_id, car_in)
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return car


@cars_router.delete("/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    """Удалить автомобиль."""
    if not crud.delete_car(db, car_id):
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    return {"message": "Car deleted"}


# --- Эндпоинты: перемещения ---

@movements_router.post("", response_model=schemas.MovementResponse, status_code=201)
def create_movement(body: MovementCreateBody, db: Session = Depends(get_db)):
    """Создать перемещение автомобиля по VIN."""
    car = crud.get_car_by_vin(db, body.vin)
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    if car.status == "продан":
        raise HTTPException(status_code=400, detail="Автомобиль уже продан")
    date_val = body.date if body.date is not None else datetime.utcnow()
    movement = crud.move_car(
        db,
        vin=body.vin,
        from_location=body.from_location,
        to_location=body.to_location,
        date=date_val,
    )
    if not movement:
        raise HTTPException(
            status_code=400,
            detail="Неверное текущее местоположение автомобиля (from_location не совпадает)",
        )
    return movement


@movements_router.get("", response_model=list[schemas.MovementResponse])
def list_movements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Получить все перемещения с пагинацией."""
    return crud.get_all_movements(db, skip=skip, limit=limit)


@movements_router.get("/car/{car_id}", response_model=list[schemas.MovementResponse])
def list_car_movements(car_id: int, db: Session = Depends(get_db)):
    """История перемещений автомобиля."""
    return crud.get_car_movements(db, car_id)


# --- Эндпоинты: продажи ---

@sales_router.post("", response_model=schemas.CarResponse, status_code=201)
def create_sale(body: SaleCreateBody, db: Session = Depends(get_db)):
    """Продать автомобиль по VIN."""
    car = crud.get_car_by_vin(db, body.vin)
    if not car:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    if car.status == "продан":
        raise HTTPException(status_code=400, detail="Автомобиль уже продан")
    sold = crud.sell_car(
        db,
        vin=body.vin,
        sale_price=body.sale_price,
        buyer_name=body.buyer_name,
        buyer_phone=body.buyer_phone,
        buyer_email=body.buyer_email,
        sale_date=body.sale_date,
    )
    return sold


@sales_router.get("", response_model=list[schemas.CarResponse])
def list_sold_cars(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """Получить все проданные автомобили (опционально по периоду)."""
    return crud.get_sold_cars(db, start_date=start_date, end_date=end_date)


# --- Эндпоинты: покупатели ---

@buyers_router.get("", response_model=list[schemas.BuyerResponse])
def list_buyers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Получить список покупателей."""
    return crud.get_buyers(db, skip=skip, limit=limit)


# --- Эндпоинты: загрузка файлов ---

def _save_upload_and_process(
    file: UploadFile,
    db: Session,
    file_type: str,
) -> dict:
    """Сохранить загруженный файл во временную директорию и вызвать process_file."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload").suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=data_dir) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = file_loader.process_file(db, tmp_path, file_type)
        parse_info = result["parse"]
        import_info = result["import"]
        errors = list(parse_info.get("errors", [])) + list(import_info.get("errors", []))
        return {
            "filename": file.filename or "upload",
            "parsed": parse_info.get("data_count", 0),
            "imported": import_info.get("imported", 0),
            "skipped": import_info.get("skipped", 0),
            "errors": errors,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _detect_file_type(file_path: str) -> Optional[str]:
    """Определить тип CSV по первой строке (заголовкам). Разделитель — точка с запятой."""
    path = Path(file_path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline()
    headers = {h.strip() for h in first_line.split(";")}
    if headers >= {"date", "model", "color", "vin", "purchase_price"}:
        return "arrivals"
    if headers >= {"date", "vin", "from_location", "to_location"}:
        return "movements"
    if headers >= {"date", "vin", "buyer_name", "sale_price"}:
        return "sales"
    return None


@files_router.post("/upload/arrivals")
def upload_arrivals(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Загрузить CSV с поступлениями и импортировать в БД."""
    return _save_upload_and_process(file, db, "arrivals")


@files_router.post("/upload/movements")
def upload_movements(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Загрузить CSV с перемещениями и импортировать в БД."""
    return _save_upload_and_process(file, db, "movements")


@files_router.post("/upload/sales")
def upload_sales(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Загрузить CSV с продажами и импортировать в БД."""
    return _save_upload_and_process(file, db, "sales")


@files_router.post("/upload/auto")
def upload_auto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Загрузить CSV с автоматическим определением типа по заголовкам."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "upload").suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=data_dir) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        file_type = _detect_file_type(tmp_path)
        if not file_type:
            Path(tmp_path).unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="Не удалось определить тип файла по заголовкам. Ожидаются: arrivals (date;model;color;vin;purchase_price), movements (date;vin;from_location;to_location), sales (date;vin;buyer_name;sale_price)",
            )
        result = file_loader.process_file(db, tmp_path, file_type)
        parse_info = result["parse"]
        import_info = result["import"]
        errors = list(parse_info.get("errors", [])) + list(import_info.get("errors", []))
        return {
            "filename": file.filename or "upload",
            "detected_type": file_type,
            "parsed": parse_info.get("data_count", 0),
            "imported": import_info.get("imported", 0),
            "skipped": import_info.get("skipped", 0),
            "errors": errors,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# --- Эндпоинты: отчёты ---

@reports_router.get("/sales")
def report_sales(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """Отчёт о продажах за период (опционально start_date, end_date)."""
    return reports.generate_sales_report(db, start_date=start_date, end_date=end_date)


@reports_router.get("/stock")
def report_stock(db: Session = Depends(get_db)):
    """Отчёт об остатках на складе."""
    return reports.generate_stock_report(db)


@reports_router.get("/buyers")
def report_buyers(db: Session = Depends(get_db)):
    """Отчёт о покупателях и проданных автомобилях."""
    return reports.generate_buyers_report(db)


@reports_router.get("/operations", response_model=list[schemas.OperationResponse])
def list_operations(
    skip: int = 0,
    limit: int = 100,
    operation_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Журнал операций (поступление, перемещение, продажа) с пагинацией и фильтром по типу."""
    return crud.get_operations(db, skip=skip, limit=limit, operation_type=operation_type)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создание таблиц БД при старте приложения."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Car Sales Management System",
    description="API для учёта автомобилей, поступлений, перемещений и продаж. "
                "Загрузка данных из CSV, формирование отчётов.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS для работы с фронтендом (для разработки — все источники)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cars_router, prefix="/api")
app.include_router(movements_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(buyers_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(files_router, prefix="/api")


@app.get("/")
def root():
    """Корневой эндпоинт: информация об API."""
    return {
        "name": "Car Sales Management System",
        "description": "Система управления продажами автомобилей: учёт авто, поступления, перемещения, продажи, отчёты.",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "cars": "/api/cars",
            "movements": "/api/movements",
            "sales": "/api/sales",
            "buyers": "/api/buyers",
            "reports": "/api/reports",
            "files": "/api/files",
        },
    }
