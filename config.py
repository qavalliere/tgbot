import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Чтение и валидация токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or not BOT_TOKEN.strip():
    raise ValueError(
        "❌ Ошибка конфигурации: переменная BOT_TOKEN не найдена или пуста.\n"
        "Пожалуйста, создайте файл .env на основе .env.example и укажите токен вашего бота."
    )
BOT_TOKEN = BOT_TOKEN.strip()

# Чтение и валидация ID администраторов (поддержка ADMIN_IDS или ADMIN_ID)
raw_admins = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID")
if not raw_admins or not raw_admins.strip():
    raise ValueError(
        "❌ Ошибка конфигурации: переменная ADMIN_IDS (или ADMIN_ID) не найдена или пуста.\n"
        "Пожалуйста, укажите ваш Telegram ID (или несколько ID через запятую) в файле .env."
    )

ADMIN_IDS: list[int] = []
for item in raw_admins.split(","):
    clean_item = item.strip()
    if clean_item:
        try:
            ADMIN_IDS.append(int(clean_item))
        except ValueError:
            raise ValueError(
                f"❌ Ошибка конфигурации: ID администратора должен быть целым числом, получено '{clean_item}'."
            )

if not ADMIN_IDS:
    raise ValueError("❌ Ошибка конфигурации: список ADMIN_IDS пуст.")


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором бота."""
    return user_id in ADMIN_IDS


# Путь к файлу базы данных SQLite
DB_PATH = Path(os.getenv("DB_PATH", "data/bot.db"))

# Контакты бизнеса (можно переопределить через .env или изменить здесь)
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "г. Киев, ул. Центральная, 10")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE", "+380 99 123 45 67")
BUSINESS_SCHEDULE = os.getenv("BUSINESS_SCHEDULE", "Пн-Сб: 09:00 - 20:00, Вс: 10:00 - 18:00")

# Список предоставляемых услуг и цен (используется для генерации меню и клавиатур)
SERVICES: list[tuple[str, str]] = [
    ("💇 Стрижка", "500 грн"),
    ("💅 Маникюр", "700 грн"),
    ("💄 Макияж", "1000 грн"),
]
