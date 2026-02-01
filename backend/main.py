from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, init_database, engine
from backend import models  # импорт моделей

app = FastAPI(title="Система управления продажами автомобилей")

# Инициализация БД
init_database(app)

# Пример эндпоинта с использованием зависимости БД
@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    """
    Тестовый эндпоинт для проверки подключения к БД
    """
    try:
        # Простой запрос для проверки соединения
        result = db.execute("SELECT 1")
        return {
            "status": "success",
            "message": "База данных подключена успешно",
            "database_url": str(engine.url)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка подключения к БД: {str(e)}"
        }