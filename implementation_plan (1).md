# План имплементации: Система управления продажами автомобилей

## Общая информация

**Технологический стек (рекомендуемый):**
- Backend: Python 3.11+ с FastAPI
- База данных: SQLite (для простоты, легко мигрировать на PostgreSQL)
- Frontend: HTML + CSS + JavaScript (Vanilla или с использованием Bootstrap)
- ORM: SQLAlchemy

**Структура проекта:**
```
car_sales_system/
├── backend/
│   ├── main.py              # Точка входа FastAPI
│   ├── database.py          # Настройка БД
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── crud.py              # CRUD операции
│   ├── file_loader.py       # Модуль загрузки файлов
│   └── reports.py           # Модуль отчётности
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/                    # Папка для входных файлов
│   ├── arrivals.csv         # Пример файла поступлений
│   ├── movements.csv        # Пример файла перемещений
│   └── sales.csv            # Пример файла продаж
├── tests/                   # Тесты
│   └── test_*.py
├── requirements.txt
└── README.md
```

---

## Этап 1: Инициализация проекта и база данных

### Шаг 1.1: Создание структуры проекта и зависимостей

**Промпт для DeepSeek:**
```
Создай requirements.txt для Python проекта "Система управления продажами автомобилей" со следующими зависимостями:
- FastAPI для REST API
- Uvicorn для сервера
- SQLAlchemy для ORM
- Pydantic для валидации
- python-multipart для загрузки файлов

Также создай базовую структуру папок и README.md с описанием проекта.
```

**Как проверить:**
1. Создать папку проекта и скопировать файлы
2. Выполнить в терминале: `pip install -r requirements.txt`
3. Убедиться, что все пакеты установились без ошибок
4. Проверить наличие всех папок

---

### Шаг 1.2: Настройка подключения к базе данных

**Промпт для DeepSeek:**
```
Создай файл backend/database.py для подключения к SQLite базе данных с использованием SQLAlchemy.

Требования:
- Путь к БД: ./car_sales.db
- Создать движок (engine) с настройками для SQLite
- Создать фабрику сессий (SessionLocal)
- Создать Base для декларативных моделей
- Добавить функцию get_db() для dependency injection в FastAPI
```

**Как проверить:**
1. Создать файл `backend/database.py`
2. Запустить Python и выполнить:
```python
from backend.database import engine, SessionLocal
print("Database engine created:", engine)
session = SessionLocal()
print("Session created successfully")
session.close()
```
3. Должен появиться файл `car_sales.db` в корне проекта

---

### Шаг 1.3: Создание моделей базы данных

**Промпт для DeepSeek:**
```
Создай файл backend/models.py с SQLAlchemy моделями для системы управления продажами автомобилей.

Модели:

1. Car (Автомобиль):
   - id: Integer, primary key, autoincrement
   - vin: String(17), unique, not null - VIN-код
   - model: String(100), not null - модель автомобиля
   - color: String(50), not null - цвет
   - purchase_price: Float, not null - цена закупки
   - sale_price: Float, nullable - цена продажи
   - status: String(20), default="на складе" - статус (на складе, продан, в демозале, на сервисе)
   - location: String(100), default="склад" - текущее местоположение
   - arrival_date: DateTime, not null - дата поступления
   - sale_date: DateTime, nullable - дата продажи
   - buyer_id: Integer, ForeignKey to Buyer, nullable

2. Movement (Перемещение):
   - id: Integer, primary key, autoincrement
   - car_id: Integer, ForeignKey to Car, not null
   - date: DateTime, not null
   - from_location: String(100), not null
   - to_location: String(100), not null
   - relationship с Car

3. Buyer (Покупатель):
   - id: Integer, primary key, autoincrement
   - name: String(200), not null - ФИО
   - phone: String(20), nullable - телефон
   - email: String(100), nullable - email
   - relationship с Car (one-to-many)

4. Operation (Операция/Лог):
   - id: Integer, primary key, autoincrement
   - car_id: Integer, ForeignKey to Car, nullable
   - operation_type: String(50), not null - тип (поступление, перемещение, продажа)
   - date: DateTime, not null
   - details: Text, nullable - детали операции
   - user: String(100), default="system"

Используй импорт из database.py. Добавь __tablename__ для каждой модели.
```

**Как проверить:**
1. Создать файл `backend/models.py`
2. Запустить Python:
```python
from backend.database import engine, Base
from backend.models import Car, Movement, Buyer, Operation

# Создать все таблицы
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# Проверить таблицы
from sqlalchemy import inspect
inspector = inspect(engine)
print("Tables:", inspector.get_table_names())
```
3. Должны появиться 4 таблицы: cars, movements, buyers, operations

---

### Шаг 1.4: Создание Pydantic схем

**Промпт для DeepSeek:**
```
Создай файл backend/schemas.py с Pydantic моделями (схемами) для валидации данных.

Создай схемы для:

1. Car:
   - CarBase (базовые поля: vin, model, color, purchase_price)
   - CarCreate (для создания, наследует CarBase + arrival_date)
   - CarUpdate (для обновления, все поля Optional)
   - CarResponse (полная модель с id и всеми полями, orm_mode=True)
   - CarSale (для продажи: sale_price, buyer_name, buyer_phone, buyer_email)

2. Movement:
   - MovementBase (car_id или vin, from_location, to_location, date)
   - MovementCreate (наследует MovementBase)
   - MovementResponse (с id, orm_mode=True)

3. Buyer:
   - BuyerBase (name, phone, email)
   - BuyerCreate (наследует BuyerBase)
   - BuyerResponse (с id и списком проданных автомобилей, orm_mode=True)

4. Operation:
   - OperationResponse (для отображения логов, orm_mode=True)

5. Reports:
   - SalesReportItem (model, color, count, total_sum)
   - SalesReport (period, total_count, total_sum, items: List[SalesReportItem])
   - StockReportItem (model, color, count, cars: List)
   - StockReport (total_count, items: List[StockReportItem])

Используй from datetime import datetime и from typing import Optional, List.
В Pydantic v2 используй model_config = ConfigDict(from_attributes=True) вместо orm_mode.
```

**Как проверить:**
1. Создать файл `backend/schemas.py`
2. Запустить Python:
```python
from backend.schemas import CarCreate, CarResponse, SalesReport
from datetime import datetime

# Тест валидации
car = CarCreate(
    vin="XYZ123456789",
    model="WOW",
    color="белый",
    purchase_price=3500000,
    arrival_date=datetime.now()
)
print("Car created:", car.model_dump())
```
3. Не должно быть ошибок импорта и валидации

---

## Этап 2: CRUD операции и бизнес-логика

### Шаг 2.1: Базовые CRUD операции для автомобилей

**Промпт для DeepSeek:**
```
Создай файл backend/crud.py с CRUD операциями для системы управления автомобилями.

Функции для автомобилей:
1. create_car(db: Session, car: CarCreate) -> Car
   - Создать новый автомобиль
   - Автоматически создать запись в Operation с типом "поступление"

2. get_car(db: Session, car_id: int) -> Car | None
   - Получить автомобиль по ID

3. get_car_by_vin(db: Session, vin: str) -> Car | None
   - Получить автомобиль по VIN

4. get_cars(db: Session, skip: int = 0, limit: int = 100) -> List[Car]
   - Получить список автомобилей с пагинацией

5. get_cars_in_stock(db: Session) -> List[Car]
   - Получить только автомобили со статусом "на складе"

6. update_car(db: Session, car_id: int, car_update: CarUpdate) -> Car | None
   - Обновить данные автомобиля

7. delete_car(db: Session, car_id: int) -> bool
   - Удалить автомобиль (мягкое или жёсткое удаление)

Используй импорты из models.py, schemas.py и database.py.
```

**Как проверить:**
1. Создать файл `backend/crud.py`
2. Запустить тест:
```python
from backend.database import SessionLocal
from backend.crud import create_car, get_car, get_cars_in_stock
from backend.schemas import CarCreate
from datetime import datetime

db = SessionLocal()

# Создать тестовый автомобиль
car_data = CarCreate(
    vin="TEST123456789",
    model="TestModel",
    color="красный",
    purchase_price=2000000,
    arrival_date=datetime.now()
)
car = create_car(db, car_data)
print(f"Created car ID: {car.id}, VIN: {car.vin}")

# Получить автомобиль
fetched = get_car(db, car.id)
print(f"Fetched car: {fetched.model}")

# Получить автомобили на складе
in_stock = get_cars_in_stock(db)
print(f"Cars in stock: {len(in_stock)}")

db.close()
```

---

### Шаг 2.2: Операции перемещения

**Промпт для DeepSeek:**
```
Добавь в файл backend/crud.py функции для работы с перемещениями автомобилей:

1. move_car(db: Session, vin: str, from_location: str, to_location: str, date: datetime) -> Movement | None
   - Найти автомобиль по VIN
   - Проверить, что текущее местоположение совпадает с from_location (или пропустить проверку если from_location пустой)
   - Создать запись Movement
   - Обновить location автомобиля на to_location
   - Обновить status автомобиля в зависимости от to_location:
     * "склад" -> статус "на складе"
     * "демозал" -> статус "в демозале"
     * "сервис" -> статус "на сервисе"
   - Создать запись в Operation с типом "перемещение"
   - Вернуть Movement или None если автомобиль не найден

2. get_car_movements(db: Session, car_id: int) -> List[Movement]
   - Получить историю перемещений автомобиля

3. get_all_movements(db: Session, skip: int = 0, limit: int = 100) -> List[Movement]
   - Получить все перемещения с пагинацией
```

**Как проверить:**
```python
from backend.database import SessionLocal
from backend.crud import move_car, get_car_movements, get_car_by_vin
from datetime import datetime

db = SessionLocal()

# Переместить тестовый автомобиль
movement = move_car(
    db,
    vin="TEST123456789",
    from_location="склад",
    to_location="демозал",
    date=datetime.now()
)
if movement:
    print(f"Movement created: {movement.from_location} -> {movement.to_location}")
    
    # Проверить обновление статуса
    car = get_car_by_vin(db, "TEST123456789")
    print(f"Car status: {car.status}, location: {car.location}")
    
    # Получить историю
    history = get_car_movements(db, car.id)
    print(f"Movement history count: {len(history)}")
else:
    print("Car not found!")

db.close()
```

---

### Шаг 2.3: Операции продажи

**Промпт для DeepSeek:**
```
Добавь в файл backend/crud.py функции для работы с продажами:

1. sell_car(db: Session, vin: str, sale_price: float, buyer_name: str, buyer_phone: str = None, buyer_email: str = None, sale_date: datetime = None) -> Car | None
   - Найти автомобиль по VIN
   - Проверить, что автомобиль не продан (status != "продан")
   - Создать или найти покупателя по имени
   - Обновить автомобиль:
     * status = "продан"
     * sale_price = переданная цена
     * sale_date = переданная дата или текущая
     * buyer_id = id покупателя
   - Создать запись в Operation с типом "продажа"
   - Вернуть обновлённый автомобиль

2. get_sold_cars(db: Session, start_date: datetime = None, end_date: datetime = None) -> List[Car]
   - Получить проданные автомобили
   - Если указаны даты - фильтровать по периоду

3. create_buyer(db: Session, buyer: BuyerCreate) -> Buyer
   - Создать нового покупателя

4. get_buyer_by_name(db: Session, name: str) -> Buyer | None
   - Найти покупателя по имени

5. get_buyers(db: Session, skip: int = 0, limit: int = 100) -> List[Buyer]
   - Получить список покупателей
```

**Как проверить:**
```python
from backend.database import SessionLocal
from backend.crud import sell_car, get_sold_cars, create_car
from backend.schemas import CarCreate
from datetime import datetime

db = SessionLocal()

# Создать автомобиль для продажи
car_data = CarCreate(
    vin="SALE123456789",
    model="WOW",
    color="белый",
    purchase_price=3500000,
    arrival_date=datetime.now()
)
car = create_car(db, car_data)

# Продать автомобиль
sold = sell_car(
    db,
    vin="SALE123456789",
    sale_price=4000000,
    buyer_name="Иванов Иван Иванович",
    buyer_phone="+7 999 123-45-67"
)
if sold:
    print(f"Car sold! Status: {sold.status}")
    print(f"Profit: {sold.sale_price - sold.purchase_price}")
else:
    print("Sale failed!")

# Проверить проданные
sold_cars = get_sold_cars(db)
print(f"Total sold cars: {len(sold_cars)}")

db.close()
```

---

## Этап 3: Модуль загрузки файлов

### Шаг 3.1: Парсер CSV файлов

**Промпт для DeepSeek:**
```
Создай файл backend/file_loader.py с функциями для загрузки данных из CSV файлов.

Форматы файлов (разделитель - точка с запятой):

1. Поступления (arrivals):
   date;model;color;vin;purchase_price
   2024-01-15;WOW;белый;XYZ123456789;3500000

2. Перемещения (movements):
   date;vin;from_location;to_location
   2024-01-16;XYZ123456789;склад;демозал

3. Продажи (sales):
   date;vin;buyer_name;sale_price
   2024-01-20;XYZ123456789;Иванов Иван Иванович;4000000

Функции:

1. parse_arrivals_file(file_path: str) -> List[dict]
   - Прочитать CSV файл с поступлениями
   - Валидировать каждую строку
   - Вернуть список словарей с данными
   - Логировать ошибки

2. parse_movements_file(file_path: str) -> List[dict]
   - Прочитать CSV файл с перемещениями
   - Валидировать каждую строку
   - Вернуть список словарей

3. parse_sales_file(file_path: str) -> List[dict]
   - Прочитать CSV файл с продажами
   - Валидировать каждую строку
   - Вернуть список словарей

4. validate_vin(vin: str) -> bool
   - Проверить формат VIN (17 символов, буквы и цифры)

5. validate_date(date_str: str) -> datetime | None
   - Парсить дату из строки (формат YYYY-MM-DD)

Используй модуль csv для парсинга. Обрабатывай ошибки и возвращай информативные сообщения.
Добавь dataclass FileLoadResult для результата с полями: success, data, errors.
```

**Как проверить:**
1. Создать тестовый файл `data/test_arrivals.csv`:
```csv
date;model;color;vin;purchase_price
2024-01-15;WOW;белый;XYZ12345678901234;3500000
2024-01-15;WOW;чёрный;XYZ98765432109876;3550000
```

2. Запустить тест:
```python
from backend.file_loader import parse_arrivals_file

result = parse_arrivals_file("data/test_arrivals.csv")
if result.success:
    print(f"Loaded {len(result.data)} records")
    for item in result.data:
        print(f"  - {item['model']} ({item['color']}): {item['vin']}")
else:
    print("Errors:", result.errors)
```

---

### Шаг 3.2: Импорт данных в базу

**Промпт для DeepSeek:**
```
Добавь в файл backend/file_loader.py функции для импорта распарсенных данных в базу:

1. import_arrivals(db: Session, data: List[dict]) -> dict
   - Принять список данных о поступлениях
   - Для каждой записи создать автомобиль через crud.create_car
   - Пропускать дубликаты VIN
   - Вернуть статистику: {"imported": int, "skipped": int, "errors": List[str]}

2. import_movements(db: Session, data: List[dict]) -> dict
   - Принять список данных о перемещениях
   - Для каждой записи вызвать crud.move_car
   - Вернуть статистику

3. import_sales(db: Session, data: List[dict]) -> dict
   - Принять список данных о продажах
   - Для каждой записи вызвать crud.sell_car
   - Вернуть статистику

4. process_file(db: Session, file_path: str, file_type: str) -> dict
   - Определить тип файла (arrivals/movements/sales)
   - Вызвать соответствующий парсер
   - Вызвать соответствующий импорт
   - Вернуть полный результат с парсингом и импортом
```

**Как проверить:**
```python
from backend.database import SessionLocal, Base, engine
from backend.file_loader import process_file
from backend import models  # Для создания таблиц

# Пересоздать БД для чистого теста
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Импортировать поступления
result = process_file(db, "data/test_arrivals.csv", "arrivals")
print("Import result:", result)

# Проверить что автомобили в БД
from backend.crud import get_cars
cars = get_cars(db)
print(f"Cars in DB: {len(cars)}")
for car in cars:
    print(f"  - {car.vin}: {car.model} ({car.color})")

db.close()
```

---

## Этап 4: Модуль отчётности

### Шаг 4.1: Отчёт о продажах

**Промпт для DeepSeek:**
```
Создай файл backend/reports.py с функциями генерации отчётов.

1. generate_sales_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> dict
   Отчёт о продажах:
   - Общее количество проданных автомобилей за период
   - Общая сумма продаж
   - Детализация по моделям: модель, количество, сумма
   - Средняя цена продажи
   - Общая прибыль (сумма продаж - сумма закупок)

   Формат возврата:
   {
       "period": {"start": date, "end": date},
       "total_count": int,
       "total_sales": float,
       "total_profit": float,
       "average_price": float,
       "by_model": [
           {"model": str, "count": int, "total": float, "profit": float}
       ]
   }

Используй SQLAlchemy queries с group_by и func.sum, func.count.
```

**Как проверить:**
```python
from backend.database import SessionLocal
from backend.reports import generate_sales_report
from datetime import datetime

db = SessionLocal()

report = generate_sales_report(db)
print("=== ОТЧЁТ О ПРОДАЖАХ ===")
print(f"Всего продано: {report['total_count']} авто")
print(f"Сумма продаж: {report['total_sales']:,.0f} руб.")
print(f"Прибыль: {report['total_profit']:,.0f} руб.")
print("\nПо моделям:")
for item in report['by_model']:
    print(f"  {item['model']}: {item['count']} шт., {item['total']:,.0f} руб.")

db.close()
```

---

### Шаг 4.2: Отчёт об остатках

**Промпт для DeepSeek:**
```
Добавь в backend/reports.py функцию отчёта об остатках:

2. generate_stock_report(db: Session) -> dict
   Отчёт об остатках на складе:
   - Общее количество автомобилей в наличии
   - Общая стоимость запасов (по закупочным ценам)
   - Группировка по моделям и цветам
   - Список конкретных автомобилей для каждой группы

   Формат возврата:
   {
       "total_count": int,
       "total_value": float,
       "by_model": [
           {
               "model": str,
               "count": int,
               "value": float,
               "by_color": [
                   {
                       "color": str,
                       "count": int,
                       "cars": [
                           {"vin": str, "purchase_price": float, "location": str}
                       ]
                   }
               ]
           }
       ]
   }

Включать только автомобили со статусом != "продан".
```

**Как проверить:**
```python
from backend.database import SessionLocal
from backend.reports import generate_stock_report

db = SessionLocal()

report = generate_stock_report(db)
print("=== ОСТАТКИ НА СКЛАДЕ ===")
print(f"Всего автомобилей: {report['total_count']}")
print(f"Общая стоимость: {report['total_value']:,.0f} руб.")
print("\nПо моделям:")
for model_data in report['by_model']:
    print(f"\n{model_data['model']}: {model_data['count']} шт.")
    for color_data in model_data['by_color']:
        print(f"  - {color_data['color']}: {color_data['count']} шт.")
        for car in color_data['cars']:
            print(f"      VIN: {car['vin']}, Локация: {car['location']}")

db.close()
```

---

### Шаг 4.3: Отчёт о покупателях и продажах

**Промпт для DeepSeek:**
```
Добавь в backend/reports.py функцию детального отчёта о продажах:

3. generate_buyers_report(db: Session) -> dict
   Отчёт о покупателях и проданных автомобилях:
   - Список всех покупателей
   - Для каждого покупателя - список купленных автомобилей с деталями

   Формат возврата:
   {
       "total_buyers": int,
       "buyers": [
           {
               "name": str,
               "phone": str,
               "email": str,
               "purchases_count": int,
               "total_spent": float,
               "cars": [
                   {
                       "vin": str,
                       "model": str,
                       "color": str,
                       "sale_price": float,
                       "sale_date": str,
                       "profit": float  # sale_price - purchase_price
                   }
               ]
           }
       ]
   }

Сортировать покупателей по сумме покупок (от большей к меньшей).
```

**Как проверить:**
```python
from backend.database import SessionLocal
from backend.reports import generate_buyers_report

db = SessionLocal()

report = generate_buyers_report(db)
print("=== ИНФОРМАЦИЯ О ПОКУПАТЕЛЯХ ===")
print(f"Всего покупателей: {report['total_buyers']}")
print("\nДетали:")
for buyer in report['buyers']:
    print(f"\n{buyer['name']}")
    print(f"  Телефон: {buyer['phone']}")
    print(f"  Покупок: {buyer['purchases_count']} на сумму {buyer['total_spent']:,.0f} руб.")
    for car in buyer['cars']:
        print(f"    - {car['model']} ({car['color']}): {car['sale_price']:,.0f} руб.")

db.close()
```

---

## Этап 5: REST API

### Шаг 5.1: Базовая структура FastAPI

**Промпт для DeepSeek:**
```
Создай файл backend/main.py с FastAPI приложением.

Требования:
- Импортировать все необходимые модули
- Создать экземпляр FastAPI с названием "Car Sales Management System" и описанием
- Настроить CORS для работы с фронтендом (allow all origins для разработки)
- Добавить событие startup для создания таблиц БД
- Добавить корневой эндпоинт GET / с информацией об API

Структура:
- Используй APIRouter для группировки эндпоинтов по категориям
- Подготовь роутеры: cars_router, movements_router, sales_router, reports_router, files_router
```

**Как проверить:**
1. Создать файл `backend/main.py`
2. Запустить сервер:
```bash
cd backend
uvicorn main:app --reload
```
3. Открыть в браузере http://localhost:8000
4. Проверить Swagger документацию: http://localhost:8000/docs

---

### Шаг 5.2: API эндпоинты для автомобилей

**Промпт для DeepSeek:**
```
Добавь в backend/main.py эндпоинты для работы с автомобилями (cars_router):

1. GET /api/cars - получить список всех автомобилей
   - Query параметры: skip (default 0), limit (default 100), status (optional: "на складе", "продан", etc.)
   - Возвращает: List[CarResponse]

2. GET /api/cars/{car_id} - получить автомобиль по ID
   - Возвращает: CarResponse
   - 404 если не найден

3. GET /api/cars/vin/{vin} - получить автомобиль по VIN
   - Возвращает: CarResponse
   - 404 если не найден

4. POST /api/cars - создать новый автомобиль
   - Body: CarCreate
   - Возвращает: CarResponse
   - 400 если VIN уже существует

5. PUT /api/cars/{car_id} - обновить автомобиль
   - Body: CarUpdate
   - Возвращает: CarResponse
   - 404 если не найден

6. DELETE /api/cars/{car_id} - удалить автомобиль
   - Возвращает: {"message": "Car deleted"}
   - 404 если не найден

7. GET /api/cars/stock - получить автомобили на складе
   - Возвращает: List[CarResponse]

Используй Depends(get_db) для получения сессии БД.
```

**Как проверить:**
1. Запустить сервер: `uvicorn main:app --reload`
2. Открыть http://localhost:8000/docs
3. Протестировать каждый эндпоинт через Swagger UI:
   - Создать автомобиль через POST /api/cars
   - Получить список через GET /api/cars
   - Получить по ID и VIN
   - Обновить и удалить

---

### Шаг 5.3: API эндпоинты для перемещений и продаж

**Промпт для DeepSeek:**
```
Добавь в backend/main.py эндпоинты для перемещений и продаж:

Перемещения (movements_router):

1. POST /api/movements - создать перемещение
   - Body: {"vin": str, "from_location": str, "to_location": str, "date": datetime (optional)}
   - Возвращает: MovementResponse
   - 404 если автомобиль не найден
   - 400 если автомобиль уже продан

2. GET /api/movements - получить все перемещения
   - Query: skip, limit
   - Возвращает: List[MovementResponse]

3. GET /api/movements/car/{car_id} - история перемещений автомобиля
   - Возвращает: List[MovementResponse]

Продажи (sales_router):

4. POST /api/sales - продать автомобиль
   - Body: {"vin": str, "sale_price": float, "buyer_name": str, "buyer_phone": str (optional), "buyer_email": str (optional), "sale_date": datetime (optional)}
   - Возвращает: CarResponse с данными о продаже
   - 404 если автомобиль не найден
   - 400 если автомобиль уже продан

5. GET /api/sales - получить все проданные автомобили
   - Query: start_date (optional), end_date (optional)
   - Возвращает: List[CarResponse]

6. GET /api/buyers - получить список покупателей
   - Возвращает: List[BuyerResponse]
```

**Как проверить:**
1. Через Swagger UI:
   - Создать перемещение для существующего автомобиля
   - Проверить историю перемещений
   - Продать автомобиль
   - Получить список проданных

---

### Шаг 5.4: API эндпоинты для отчётов

**Промпт для DeepSeek:**
```
Добавь в backend/main.py эндпоинты для отчётов (reports_router):

1. GET /api/reports/sales - отчёт о продажах
   - Query: start_date (optional), end_date (optional)
   - Возвращает: SalesReport

2. GET /api/reports/stock - отчёт об остатках
   - Возвращает: StockReport

3. GET /api/reports/buyers - отчёт о покупателях
   - Возвращает: BuyersReport

4. GET /api/reports/operations - журнал операций
   - Query: skip, limit, operation_type (optional)
   - Возвращает: List[OperationResponse]
```

**Как проверить:**
1. Через Swagger UI вызвать каждый эндпоинт отчётов
2. Проверить что данные соответствуют созданным ранее автомобилям и операциям

---

### Шаг 5.5: API эндпоинты для загрузки файлов

**Промпт для DeepSeek:**
```
Добавь в backend/main.py эндпоинты для загрузки файлов (files_router):

1. POST /api/files/upload/arrivals - загрузить файл поступлений
   - Принимает: UploadFile
   - Сохраняет файл во временную директорию
   - Вызывает process_file с типом "arrivals"
   - Возвращает: {"filename": str, "parsed": int, "imported": int, "skipped": int, "errors": List[str]}

2. POST /api/files/upload/movements - загрузить файл перемещений
   - Аналогично, тип "movements"

3. POST /api/files/upload/sales - загрузить файл продаж
   - Аналогично, тип "sales"

4. POST /api/files/upload/auto - автоматическое определение типа файла
   - Определить тип по заголовкам CSV
   - Вызвать соответствующую обработку

Используй aiofiles или стандартную запись для сохранения файлов.
Создавай директорию data если не существует.
```

**Как проверить:**
1. Создать тестовые CSV файлы в папке data
2. Через Swagger UI загрузить файл (используя форму upload)
3. Проверить что данные импортировались в БД
4. Проверить ответ с количеством импортированных записей

---

## Этап 6: Frontend

### Шаг 6.1: HTML структура

**Промпт для DeepSeek:**
```
Создай файл frontend/index.html для системы управления продажами автомобилей.

Требования:
- Современный адаптивный дизайн
- Навигация с вкладками: Автомобили, Перемещения, Продажи, Отчёты, Загрузка файлов
- Секции для каждой вкладки:
  
1. Автомобили:
   - Таблица со списком автомобилей (VIN, модель, цвет, цена, статус, локация)
   - Кнопка "Добавить автомобиль"
   - Фильтр по статусу

2. Перемещения:
   - Форма создания перемещения (выбор автомобиля, откуда, куда)
   - История перемещений

3. Продажи:
   - Форма продажи (выбор автомобиля, цена, данные покупателя)
   - Список проданных автомобилей

4. Отчёты:
   - Кнопки для генерации отчётов
   - Область отображения отчёта

5. Загрузка файлов:
   - Drag-and-drop зона для файлов
   - Выбор типа файла
   - Результат загрузки

Используй семантический HTML5. Подключи Bootstrap 5 через CDN для стилей.
Подключи app.js в конце body.
```

**Как проверить:**
1. Открыть `frontend/index.html` в браузере
2. Проверить что все вкладки отображаются
3. Проверить адаптивность (resize окна)
4. Проверить что Bootstrap стили применяются

---

### Шаг 6.2: CSS стили

**Промпт для DeepSeek:**
```
Создай файл frontend/styles.css с кастомными стилями для системы.

Требования:
- Цветовая схема: профессиональная, автомобильная тематика (тёмно-синий, серый, белый, акценты оранжевого)
- Кастомизация Bootstrap компонентов
- Стили для:
  - Навигации
  - Карточек с информацией
  - Таблиц данных
  - Форм ввода
  - Модальных окон
  - Области drag-and-drop
  - Статус-бейджей (на складе - зелёный, продан - красный, в демозале - синий, на сервисе - жёлтый)
- Анимации для интерактивных элементов
- Адаптивные стили для мобильных устройств

Добавь CSS переменные для основных цветов.
```

**Как проверить:**
1. Подключить styles.css в index.html
2. Обновить страницу и проверить что стили применяются
3. Проверить цвета, отступы, анимации
4. Проверить на мобильном разрешении

---

### Шаг 6.3: JavaScript - базовая структура и API

**Промпт для DeepSeek:**
```
Создай файл frontend/app.js с базовой структурой JavaScript приложения.

Структура:
1. Константа API_BASE_URL = 'http://localhost:8000/api'

2. Класс или объект API с методами:
   - async fetchCars(status = null)
   - async fetchCarById(id)
   - async fetchCarByVin(vin)
   - async createCar(carData)
   - async updateCar(id, carData)
   - async deleteCar(id)
   - async createMovement(movementData)
   - async fetchMovements()
   - async sellCar(saleData)
   - async fetchSales()
   - async fetchReportSales(startDate, endDate)
   - async fetchReportStock()
   - async fetchReportBuyers()
   - async uploadFile(file, fileType)

Каждый метод должен:
- Использовать fetch с async/await
- Обрабатывать ошибки
- Возвращать JSON ответ или выбрасывать исключение

3. Функция showNotification(message, type) - показ уведомлений (success, error, info)

4. Функция formatCurrency(amount) - форматирование суммы в рубли

5. DOMContentLoaded слушатель для инициализации
```

**Как проверить:**
1. Добавить app.js в проект
2. Открыть браузер, открыть DevTools Console
3. Ввести: `await API.fetchCars()` (должен вернуть массив или ошибку если сервер не запущен)
4. Запустить сервер и повторить - должен вернуть данные

---

### Шаг 6.4: JavaScript - отображение данных

**Промпт для DeepSeek:**
```
Добавь в frontend/app.js функции для отображения данных:

1. Функция renderCarsTable(cars)
   - Очистить tbody таблицы автомобилей
   - Для каждого автомобиля создать строку с данными
   - Добавить бейдж статуса с соответствующим цветом
   - Добавить кнопки действий (просмотр, переместить, продать, удалить)
   - Использовать template literals для HTML

2. Функция renderMovementsTable(movements)
   - Отобразить историю перемещений

3. Функция renderSalesTable(sales)
   - Отобразить список продаж с данными покупателей

4. Функция renderReport(reportData, reportType)
   - В зависимости от типа отчёта отформатировать и отобразить данные
   - Использовать карточки Bootstrap для группировки

5. Функция initNavigation()
   - Переключение между вкладками
   - При переключении загружать соответствующие данные

6. Функция loadInitialData()
   - Загрузить и отобразить автомобили при старте

Вызвать initNavigation() и loadInitialData() в DOMContentLoaded.
```

**Как проверить:**
1. Запустить backend сервер
2. Открыть index.html в браузере
3. Должна загрузиться таблица автомобилей (или пустая если нет данных)
4. Переключить вкладки - данные должны загружаться

---

### Шаг 6.5: JavaScript - формы и модальные окна

**Промпт для DeepSeek:**
```
Добавь в frontend/app.js обработчики форм:

1. Модальное окно и форма добавления автомобиля:
   - Открытие модального окна по кнопке "Добавить"
   - Поля: VIN, модель, цвет, цена закупки, дата поступления
   - Валидация полей (VIN 17 символов, цена > 0)
   - Отправка данных через API.createCar()
   - Закрытие модального окна и обновление таблицы после успеха
   - Показ ошибок при неудаче

2. Форма перемещения:
   - Выпадающий список автомобилей (только доступные для перемещения)
   - Поля: откуда, куда
   - Отправка через API.createMovement()
   - Обновление данных после успеха

3. Форма продажи:
   - Выпадающий список автомобилей (только на складе/в демозале)
   - Поля: цена продажи, ФИО покупателя, телефон, email
   - Валидация (цена > 0, ФИО обязательно)
   - Отправка через API.sellCar()
   - Обновление данных после успеха

4. Обработчики кнопок действий в таблице:
   - Просмотр деталей (модальное окно с полной информацией)
   - Быстрое перемещение
   - Быстрая продажа
   - Удаление с подтверждением
```

**Как проверить:**
1. Открыть приложение в браузере
2. Нажать "Добавить автомобиль" - должно открыться модальное окно
3. Заполнить форму и отправить - автомобиль должен появиться в таблице
4. Проверить валидацию - ввести неверный VIN
5. Попробовать переместить и продать автомобиль

---

### Шаг 6.6: JavaScript - загрузка файлов

**Промпт для DeepSeek:**
```
Добавь в frontend/app.js функционал загрузки файлов:

1. Функция initFileUpload()
   - Найти drop-zone элемент
   - Добавить обработчики drag events (dragover, dragleave, drop)
   - Визуальная индикация при перетаскивании
   - Обработка сброшенного файла

2. Функция handleFileSelect(file, fileType)
   - Проверить расширение файла (.csv, .txt)
   - Показать имя файла и размер
   - Вызвать uploadFile()

3. Функция uploadFile(file, fileType)
   - Показать индикатор загрузки
   - Отправить файл через API.uploadFile()
   - Отобразить результат: сколько записей импортировано, пропущено, ошибки
   - Предложить просмотреть импортированные данные

4. Функция displayUploadResult(result)
   - Отформатировать результат загрузки
   - Показать статистику
   - Список ошибок если есть

5. Радио-кнопки или select для выбора типа файла:
   - Поступления
   - Перемещения  
   - Продажи
   - Автоопределение

Добавить вызов initFileUpload() в DOMContentLoaded.
```

**Как проверить:**
1. Открыть вкладку "Загрузка файлов"
2. Перетащить CSV файл в drop-zone
3. Выбрать тип файла
4. Нажать "Загрузить"
5. Проверить результат и данные в таблице автомобилей

---

## Этап 7: Тестирование и финализация

### Шаг 7.1: Создание тестовых данных

**Промпт для DeepSeek:**
```
Создай набор тестовых CSV файлов для проверки системы:

1. data/test_arrivals.csv - 10 автомобилей:
   - 4 модели WOW разных цветов
   - 3 модели SUPER разных цветов
   - 3 модели MEGA разных цветов
   - Даты поступления в январе 2024
   - Цены от 2 000 000 до 5 000 000

2. data/test_movements.csv - 5 перемещений:
   - 2 автомобиля на демозал
   - 1 автомобиль на сервис
   - 1 автомобиль обратно на склад
   - Используй VIN из arrivals

3. data/test_sales.csv - 3 продажи:
   - 3 разных автомобиля разным покупателям
   - Цены продажи выше закупочных
   - Используй VIN из arrivals (которые не на сервисе)

Формат разделителя: точка с запятой.
```

**Как проверить:**
1. Создать файлы в папке data
2. Открыть каждый файл и проверить формат
3. Загрузить файлы через интерфейс последовательно
4. Проверить данные в таблицах
5. Проверить отчёты

---

### Шаг 7.2: Скрипт полного тестирования

**Промпт для DeepSeek:**
```
Создай файл tests/test_full_flow.py с полным тестом системы:

Тест должен:
1. Пересоздать базу данных (чистый старт)
2. Импортировать файл поступлений
3. Проверить количество автомобилей
4. Импортировать файл перемещений
5. Проверить что перемещения применились
6. Импортировать файл продаж
7. Проверить что продажи применились
8. Сгенерировать все отчёты
9. Вывести итоговую статистику

Использовать assert для проверок.
Выводить понятные сообщения о каждом этапе.
```

**Как проверить:**
```bash
cd tests
python test_full_flow.py
```
Все проверки должны пройти без ошибок.

---

### Шаг 7.3: README документация

**Промпт для DeepSeek:**
```
Обнови README.md с полной документацией проекта:

Разделы:
1. Описание проекта
2. Технологический стек
3. Установка и запуск
   - Требования
   - Установка зависимостей
   - Запуск backend
   - Открытие frontend
4. Использование
   - Загрузка данных из файлов
   - Работа с автомобилями
   - Перемещения
   - Продажи
   - Отчёты
5. API документация (ссылка на Swagger)
6. Формат входных файлов
   - Примеры CSV
7. Структура проекта
8. Лицензия

Добавь скриншоты placeholder'ы (можно добавить позже).
```

**Как проверить:**
1. Открыть README.md
2. Прочитать и проверить что все инструкции корректны
3. Следуя README установить и запустить проект с нуля

---

## Контрольный чек-лист готовности

После выполнения всех этапов проверь:

- [ ] Backend запускается без ошибок
- [ ] API документация доступна по /docs
- [ ] Frontend отображается корректно
- [ ] Можно создать автомобиль через форму
- [ ] Можно загрузить CSV файл с поступлениями
- [ ] Можно переместить автомобиль
- [ ] Можно продать автомобиль
- [ ] Отчёт о продажах формируется корректно
- [ ] Отчёт об остатках формируется корректно
- [ ] Отчёт о покупателях формируется корректно
- [ ] Все данные сохраняются между перезапусками
- [ ] Нет ошибок в консоли браузера
- [ ] Нет ошибок в логах сервера

---

## Советы по работе с DeepSeek

1. **Один шаг - один промпт**: Не пытайся делать несколько задач в одном промпте

2. **Копируй весь код**: Если DeepSeek показывает "..." для пропуска кода, попроси показать полностью

3. **Проверяй импорты**: Убедись что все import'ы есть в начале файла

4. **Ошибки = контекст**: Если что-то не работает, скопируй ошибку и отправь DeepSeek с просьбой исправить

5. **Сохраняй контекст**: Если начинаешь новый чат, опиши что уже сделано

6. **Уточняющие вопросы**: Если код непонятен, попроси DeepSeek объяснить

7. **Версии пакетов**: При ошибках импорта проверь версии в requirements.txt
