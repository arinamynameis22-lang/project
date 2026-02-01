`python
# backend/database.py
from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os
from contextlib import contextmanager

# Базовая модель для всех ORM моделей
Base = declarative_base()

class DatabaseManager:
    """Менеджер для работы с базой данных SQLite"""
    
    def init(self, database_url: str = None):
        """
        Инициализация менеджера базы данных
        
        Args:
            database_url: URL подключения к БД. По умолчанию SQLite в текущей директории
        """
        if database_url is None:
            # Путь к БД относительно текущего файла
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(file)))
            db_path = os.path.join(base_dir, "car_sales.db")
            self.database_url = f"sqlite:///{db_path}"
        else:
            self.database_url = database_url
            
        self._engine = None
        self._SessionLocal = None
        
    def get_engine(self) -> Engine:
        """Создает и возвращает движок SQLAlchemy"""
        if self._engine is None:
            # Конфигурация для SQLite
            connect_args = {}
            
            # SQLite требует check_same_thread=False при использовании в многопоточных приложениях
            if self.database_url.startswith("sqlite"):
                connect_args["check_same_thread"] = False
                # Для лучшей производительности можно использовать StaticPool
                connect_args["poolclass"] = StaticPool
                
            self._engine = create_engine(
                self.database_url,
                connect_args=connect_args,
                echo=False,  # Установите True для отладки SQL запросов
                pool_pre_ping=True,  # Проверка соединения перед использованием
            )
            
        return self._engine
    
    def get_session_local(self) -> sessionmaker:
        """Создает и возвращает фабрику сессий"""
        if self._SessionLocal is None:
            engine = self.get_engine()
            self._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
                expire_on_commit=True,
            )
        return self._SessionLocal
    
    def create_tables(self):
        """Создает все таблицы в базе данных"""
        engine = self.get_engine()
        Base.metadata.create_all(bind=engine)
        print(f"Таблицы созданы в базе данных: {self.database_url}")
    
    def drop_tables(self):
        """Удаляет все таблицы из базы данных (для тестирования)"""
        engine = self.get_engine()
        Base.metadata.drop_all(bind=engine)
        print(f"Таблицы удалены из базы данных: {self.database_url}")
    
    def get_db(self) -> Generator[Session, None, None]:
        """
        Генератор сессий БД для использования в FastAPI зависимостях
        
        Yields:
            SQLAlchemy Session object
        """
        SessionLocal = self.get_session_local()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @contextmanager
    def session_scope(self):
        """
        Контекстный менеджер для работы с сессиями БД.
        Автоматически коммитит изменения и откатывает при ошибках.
        
        Использование:
        with db_manager.session_scope() as session:
            # работа с сессией
        """
        SessionLocal = self.get_session_local()
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
finally:
            session.close()
    
    def close_connections(self):
        """Закрывает все соединения с базой данных"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None
    
    @property
    def session(self) -> sessionmaker:
        """Свойство для быстрого доступа к фабрике сессий"""
        return self.get_session_local()
        
# Создаем экземпляр менеджера БД с настройками по умолчанию
database_manager = DatabaseManager()

# Короткие алиасы для удобного импорта
engine = database_manager.get_engine()
SessionLocal = database_manager.get_session_local()
get_db = database_manager.get_db

# Функция для инициализации БД в приложении FastAPI
def init_database(app):
    """
    Инициализация базы данных в приложении FastAPI
    
    Args:
        app: Экземпляр FastAPI приложения
    """
    @app.on_event("startup")
    def startup_event():
        """Событие при запуске приложения"""
        # Создаем таблицы, если их нет
        database_manager.create_tables()
        print("База данных инициализирована")
    
    @app.on_event("shutdown")
    def shutdown_event():
        """Событие при завершении работы приложения"""
        database_manager.close_connections()
        print("Соединения с базой данных закрыты")


if name == "main":
    # Тестирование подключения и создание таблиц
    try:
        print("Инициализация базы данных...")
        database_manager.create_tables()
        print("База данных успешно инициализирована")
        print(f"Путь к БД: {database_manager.database_url}")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")