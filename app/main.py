import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ВАЖНО: загружаем .env до импорта менеджеров БД
from config import settings as _settings  # noqa: F401
from app.api.limits import router as limits_router
from app.api.bible import router as bible_router
from app.api.ai import router as ai_router
from app.api.chat import router as chat_router
from app.api.bookmarks import router as bookmarks_router
from app.api.plans import router as plans_router
from app.api.topics import router as topics_router


def create_app() -> FastAPI:
    app = FastAPI(title="Gospel Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://bible-plus-ai.ru",
            "https://www.bible-plus-ai.ru",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost",
            "http://127.0.0.1",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def on_startup():
        """Инициализация менеджера БД и лог типа подключения"""
        try:
            from database.universal_manager import universal_db_manager as db
            await db.initialize()
            db_type = "Supabase" if db.is_supabase else (
                "PostgreSQL" if db.is_postgres else "SQLite")
            logging.getLogger(__name__).info(
                f"[Backend] БД инициализирована: {db_type}")
        except Exception as e:
            logging.getLogger(__name__).error(
                f"[Backend] Ошибка инициализации БД: {e}")

    # Routers
    app.include_router(limits_router)
    app.include_router(bible_router)
    app.include_router(ai_router)
    app.include_router(chat_router)
    app.include_router(bookmarks_router)
    app.include_router(plans_router)
    app.include_router(topics_router)

    return app


app = create_app()
