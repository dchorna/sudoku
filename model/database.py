import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///sudoku_app.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Neon віддає postgresql://, а SQLAlchemy з psycopg3 потребує драйвера в схемі
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,   # перепідключення після засинання Neon
        pool_recycle=300,
        connect_args={"prepare_threshold": None},  # сумісність з PgBouncer
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)