from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.tasks import router as tasks_router, requirements_router
from app.api.artifacts import router as artifacts_router, summaries_router
from app.api.tree import router as tree_router
from app.api.storage import router as storage_router
from app.api.reviews import router as reviews_router
from app.api.backup import router as backup_router
from app.core.config import settings

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version
)

# APIルーターの登録
app.include_router(tasks_router)
app.include_router(requirements_router)
app.include_router(artifacts_router)
app.include_router(summaries_router)
app.include_router(tree_router)
app.include_router(storage_router)
app.include_router(reviews_router)
app.include_router(backup_router)

@app.get("/")
def read_root():
    return {"message": "TODO API Ready"}
