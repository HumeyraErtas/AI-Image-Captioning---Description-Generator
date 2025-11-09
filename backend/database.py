from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from .config import DATABASE_URL
    from .models import Base
except ImportError:
    # When running as a script
    from config import DATABASE_URL
    from models import Base

# Engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Tabloları oluşturmak için bir kere çalıştır."""
    Base.metadata.create_all(bind=engine)
