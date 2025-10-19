from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# データベースエンジンの作成
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# セッションファクトリーの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()


def get_db():
    """データベースセッションの依存性注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
