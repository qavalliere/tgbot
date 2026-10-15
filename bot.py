import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
import database
from handlers import start_router, info_router, application_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Точка входа: инициализация БД и запуск Telegram-бота в режиме Long Polling.
    """
    logger.info("Запуск Telegram-бота...")

    # Инициализация базы данных SQLite
    await database.init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров с обработчиками
    dp.include_router(start_router)
    dp.include_router(info_router)
    dp.include_router(application_router)

    try:
        # Удаляем вебхук и старые накопившиеся сообщения перед стартом
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот успешно запущен и ожидает сообщений!")
        await dp.start_polling(bot)
    except Exception as exc:
        logger.exception(f"Критическая ошибка при работе бота: {exc}")
    finally:
        logger.info("Остановка бота и закрытие сессии...")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
