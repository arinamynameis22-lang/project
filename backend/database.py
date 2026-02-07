"""
Настройка подключения к SQLite базе данных с использованием SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Путь к БД: ./car_sales.db (относительно рабочей директории)
SQLALCHEMY_DATABASE_URL = "sqlite:///./car_sales.db"

# Движок с настройками для SQLite
# check_same_thread=False — для совместимости с FastAPI (несколько потоков)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # True для отладки SQL-запросов
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для декларативных моделей
Base = declarative_base()


def get_db():
    """
    Генератор сессии БД для dependency injection в FastAPI.
    Гарантирует закрытие сессии после использования.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
