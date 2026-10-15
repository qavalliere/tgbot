import logging
from typing import Any
import aiosqlite
import config

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Инициализирует базу данных SQLite и создает необходимые таблицы.
    """
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_chat_id INTEGER NOT NULL,
                client_username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                desired_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()
    logger.info(f"База данных SQLite инициализирована: {config.DB_PATH}")


async def create_lead(
    client_chat_id: int,
    client_username: str | None,
    name: str,
    phone: str,
    service: str,
    desired_time: str,
) -> int:
    """
    Создает новую заявку в базе данных и возвращает её ID.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO leads (client_chat_id, client_username, name, phone, service, desired_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
            (client_chat_id, client_username, name, phone, service, desired_time),
        )
        await db.commit()
        lead_id = cursor.lastrowid
        return lead_id


async def get_lead(lead_id: int) -> dict[str, Any] | None:
    """
    Возвращает данные заявки по её идентификатору.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM leads WHERE id = ?",
            (lead_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def update_lead_status(lead_id: int, new_status: str) -> bool:
    """
    Обновляет статус заявки (например, 'approved' или 'rejected').
    Возвращает True, если статус был успешно обновлен.
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE leads SET status = ? WHERE id = ? AND status = 'pending'",
            (new_status, lead_id),
        )
        await db.commit()
        return cursor.rowcount > 0
