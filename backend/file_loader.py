"""
Загрузка данных из CSV-файлов (поступления, перемещения, продажи).
Разделитель — точка с запятой.
"""

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Any

from sqlalchemy.orm import Session

from backend import crud, schemas

logger = logging.getLogger(__name__)


@dataclass
class FileLoadResult:
    """Результат загрузки файла: успех, данные, список ошибок."""
    success: bool
    data: List[dict]
    errors: List[str]


def validate_vin(vin: str) -> bool:
    """Проверить формат VIN: 17 символов, буквы и цифры."""
    if not vin or len(vin) != 17:
        return False
    return vin.isalnum()


def validate_date(date_str: str) -> datetime | None:
    """Распарсить дату из строки (формат YYYY-MM-DD)."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def parse_arrivals_file(file_path: str) -> FileLoadResult:
    """
    Прочитать CSV с поступлениями.
    Колонки: date;model;color;vin;purchase_price
    """
    data: List[dict] = []
    errors: List[str] = []
    path = Path(file_path)

    if not path.exists():
        errors.append(f"Файл не найден: {file_path}")
        logger.error("File not found: %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row_num, row in enumerate(reader, start=2):
                row = {k.strip(): v for k, v in row.items()} if row else {}
                date_val = validate_date(row.get("date", ""))
                if date_val is None:
                    errors.append(f"Строка {row_num}: неверная дата '{row.get('date', '')}'")
                    logger.warning("Row %d: invalid date", row_num)
                    continue
                vin = (row.get("vin") or "").strip()
                if not validate_vin(vin):
                    errors.append(f"Строка {row_num}: неверный VIN '{vin}' (ожидается 17 букв/цифр)")
                    logger.warning("Row %d: invalid VIN", row_num)
                    continue
                try:
                    price = float((row.get("purchase_price") or "").replace(",", ".").strip())
                except (ValueError, TypeError):
                    errors.append(f"Строка {row_num}: неверная цена закупки '{row.get('purchase_price')}'")
                    continue
                model = (row.get("model") or "").strip()
                color = (row.get("color") or "").strip()
                if not model or not color:
                    errors.append(f"Строка {row_num}: модель и цвет обязательны")
                    continue
                data.append({
                    "date": date_val,
                    "model": model,
                    "color": color,
                    "vin": vin,
                    "purchase_price": price,
                })
    except OSError as e:
        errors.append(f"Ошибка чтения файла: {e}")
        logger.exception("Error reading file %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    return FileLoadResult(success=len(errors) == 0, data=data, errors=errors)


def parse_movements_file(file_path: str) -> FileLoadResult:
    """
    Прочитать CSV с перемещениями.
    Колонки: date;vin;from_location;to_location
    """
    data: List[dict] = []
    errors: List[str] = []
    path = Path(file_path)

    if not path.exists():
        errors.append(f"Файл не найден: {file_path}")
        logger.error("File not found: %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row_num, row in enumerate(reader, start=2):
                row = {k.strip(): v for k, v in row.items()} if row else {}
                date_val = validate_date(row.get("date", ""))
                if date_val is None:
                    errors.append(f"Строка {row_num}: неверная дата '{row.get('date', '')}'")
                    continue
                vin = (row.get("vin") or "").strip()
                if not validate_vin(vin):
                    errors.append(f"Строка {row_num}: неверный VIN '{vin}'")
                    continue
                from_loc = (row.get("from_location") or "").strip()
                to_loc = (row.get("to_location") or "").strip()
                if not from_loc or not to_loc:
                    errors.append(f"Строка {row_num}: from_location и to_location обязательны")
                    continue
                data.append({
                    "date": date_val,
                    "vin": vin,
                    "from_location": from_loc,
                    "to_location": to_loc,
                })
    except OSError as e:
        errors.append(f"Ошибка чтения файла: {e}")
        logger.exception("Error reading file %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    return FileLoadResult(success=len(errors) == 0, data=data, errors=errors)


def parse_sales_file(file_path: str) -> FileLoadResult:
    """
    Прочитать CSV с продажами.
    Колонки: date;vin;buyer_name;sale_price
    """
    data: List[dict] = []
    errors: List[str] = []
    path = Path(file_path)

    if not path.exists():
        errors.append(f"Файл не найден: {file_path}")
        logger.error("File not found: %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row_num, row in enumerate(reader, start=2):
                row = {k.strip(): v for k, v in row.items()} if row else {}
                date_val = validate_date(row.get("date", ""))
                if date_val is None:
                    errors.append(f"Строка {row_num}: неверная дата '{row.get('date', '')}'")
                    continue
                vin = (row.get("vin") or "").strip()
                if not validate_vin(vin):
                    errors.append(f"Строка {row_num}: неверный VIN '{vin}'")
                    continue
                buyer_name = (row.get("buyer_name") or "").strip()
                if not buyer_name:
                    errors.append(f"Строка {row_num}: buyer_name обязателен")
                    continue
                try:
                    sale_price = float((row.get("sale_price") or "").replace(",", ".").strip())
                except (ValueError, TypeError):
                    errors.append(f"Строка {row_num}: неверная цена продажи '{row.get('sale_price')}'")
                    continue
                data.append({
                    "date": date_val,
                    "vin": vin,
                    "buyer_name": buyer_name,
                    "sale_price": sale_price,
                })
    except OSError as e:
        errors.append(f"Ошибка чтения файла: {e}")
        logger.exception("Error reading file %s", file_path)
        return FileLoadResult(success=False, data=[], errors=errors)

    return FileLoadResult(success=len(errors) == 0, data=data, errors=errors)


# --- Импорт в БД ---

def import_arrivals(db: Session, data: List[dict]) -> dict[str, Any]:
    """
    Импорт поступлений в БД. Пропуск записей с дубликатом VIN.
    Возвращает: {"imported": int, "skipped": int, "errors": List[str]}
    """
    imported = 0
    skipped = 0
    errors: List[str] = []

    for item in data:
        if crud.get_car_by_vin(db, item["vin"]):
            skipped += 1
            continue
        try:
            car_in = schemas.CarCreate(
                vin=item["vin"],
                model=item["model"],
                color=item["color"],
                purchase_price=item["purchase_price"],
                arrival_date=item["date"],
            )
            crud.create_car(db, car_in)
            imported += 1
        except Exception as e:
            errors.append(f"VIN {item.get('vin', '?')}: {e}")
            logger.exception("Import arrival failed for VIN %s", item.get("vin"))

    return {"imported": imported, "skipped": skipped, "errors": errors}


def import_movements(db: Session, data: List[dict]) -> dict[str, Any]:
    """
    Импорт перемещений в БД через crud.move_car.
    Возвращает: {"imported": int, "skipped": int, "errors": List[str]}
    """
    imported = 0
    skipped = 0
    errors: List[str] = []

    for item in data:
        movement = crud.move_car(
            db,
            vin=item["vin"],
            from_location=item["from_location"],
            to_location=item["to_location"],
            date=item["date"],
        )
        if movement:
            imported += 1
        else:
            skipped += 1
            errors.append(
                f"VIN {item['vin']}: автомобиль не найден или неверное местоположение "
                f"({item['from_location']} -> {item['to_location']})"
            )

    return {"imported": imported, "skipped": skipped, "errors": errors}


def import_sales(db: Session, data: List[dict]) -> dict[str, Any]:
    """
    Импорт продаж в БД через crud.sell_car.
    Возвращает: {"imported": int, "skipped": int, "errors": List[str]}
    """
    imported = 0
    skipped = 0
    errors: List[str] = []

    for item in data:
        sold = crud.sell_car(
            db,
            vin=item["vin"],
            sale_price=item["sale_price"],
            buyer_name=item["buyer_name"],
            sale_date=item["date"],
        )
        if sold:
            imported += 1
        else:
            skipped += 1
            errors.append(
                f"VIN {item['vin']}: автомобиль не найден или уже продан"
            )

    return {"imported": imported, "skipped": skipped, "errors": errors}


def process_file(db: Session, file_path: str, file_type: str) -> dict[str, Any]:
    """
    Определить тип файла (arrivals / movements / sales), распарсить и импортировать в БД.
    Возвращает полный результат: парсинг + импорт.
    """
    file_type = file_type.lower().strip()
    if file_type not in ("arrivals", "movements", "sales"):
        return {
            "parse": {"success": False, "data_count": 0, "errors": [f"Неизвестный тип файла: {file_type}"]},
            "import": {"imported": 0, "skipped": 0, "errors": []},
        }

    if file_type == "arrivals":
        parse_result = parse_arrivals_file(file_path)
        import_result = import_arrivals(db, parse_result.data) if parse_result.data else {"imported": 0, "skipped": 0, "errors": []}
    elif file_type == "movements":
        parse_result = parse_movements_file(file_path)
        import_result = import_movements(db, parse_result.data) if parse_result.data else {"imported": 0, "skipped": 0, "errors": []}
    else:  # sales
        parse_result = parse_sales_file(file_path)
        import_result = import_sales(db, parse_result.data) if parse_result.data else {"imported": 0, "skipped": 0, "errors": []}

    return {
        "parse": {
            "success": parse_result.success,
            "data_count": len(parse_result.data),
            "errors": parse_result.errors,
        },
        "import": import_result,
    }
