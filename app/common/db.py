"""
Database connection and session management.

Supports PostgreSQL with SQLAlchemy, with CSV fallback mode.
"""

import os
from typing import Optional
from contextlib import contextmanager
from app.common.middleware import get_logger

logger = get_logger(__name__)

# Try to import SQLAlchemy (optional dependency)
try:
    from sqlalchemy import create_engine, Column, String, Float, Integer, JSON, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None
    logger.info("SQLAlchemy not available, database features disabled")


if SQLALCHEMY_AVAILABLE:
    class ProductORM(Base):
        """SQLAlchemy ORM model for products."""
        __tablename__ = "products"
        
        product_id = Column(String, primary_key=True, index=True)
        title = Column(String, nullable=False)
        description = Column(Text, nullable=False)
        price = Column(Float, nullable=False)
        category = Column(String, nullable=False, index=True)
        image_url = Column(String, nullable=True)
        metadata = Column(JSON, nullable=True)
        stock_quantity = Column(Integer, default=0)
        created_at = Column(String, nullable=True)
        updated_at = Column(String, nullable=True)
else:
    ProductORM = None

# Import LogEventORM from models.py
try:
    from app.common.models import LogEventORM
except ImportError:
    LogEventORM = None


# Database connection
_engine = None
_SessionLocal = None


def init_db(database_url: Optional[str] = None) -> bool:
    """
    Initialize database connection.
    
    Args:
        database_url: PostgreSQL connection string (e.g., postgresql://user:pass@host/db)
        
    Returns:
        True if database connection successful, False otherwise
    """
    global _engine, _SessionLocal
    
    if not SQLALCHEMY_AVAILABLE:
        logger.info("SQLAlchemy not available, will use CSV fallback mode")
        return False
    
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.info("No DATABASE_URL found, will use CSV fallback mode")
        return False
    
    try:
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # Test connection
        with _engine.connect() as conn:
            conn.execute("SELECT 1")
        
        logger.info("Database connection established successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to connect to database: {e}. Will use CSV fallback mode")
        _engine = None
        _SessionLocal = None
        return False


def get_db():  # type: ignore
    """
    Get database session.
    
    Returns:
        Database session if connection available, None otherwise
    """
    if _SessionLocal is None:
        return None
    
    db = _SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Error creating database session: {e}")
        return None


@contextmanager
def get_db_session():
    """Context manager for database session."""
    db = get_db()
    if db is None:
        yield None
        return
    
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def is_db_available() -> bool:
    """Check if database is available."""
    return _engine is not None and _SessionLocal is not None


def create_tables():
    """Create database tables if they don't exist."""
    if not SQLALCHEMY_AVAILABLE or _engine is None or Base is None:
        return False
    
    try:
        Base.metadata.create_all(bind=_engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False

