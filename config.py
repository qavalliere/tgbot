import os
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

# Чтение и валидация ID администратора (владельца бизнеса)
ADMIN_ID_RAW = os.getenv("ADMIN_ID")
if not ADMIN_ID_RAW or not ADMIN_ID_RAW.strip():
    raise ValueError(
        "❌ Ошибка конфигурации: переменная ADMIN_ID не найдена или пуста.\n"
        "Пожалуйста, укажите ваш Telegram ID в файле .env (числовой идентификатор)."
    )

try:
    ADMIN_ID = int(ADMIN_ID_RAW.strip())
except ValueError:
    raise ValueError(
        f"❌ Ошибка конфигурации: ADMIN_ID должен быть целым числом, получено '{ADMIN_ID_RAW}'."
    )

# Контакты бизнеса (можно переопределить через .env или изменить здесь)
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "г. Киев, ул. Центральная, 10")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE", "+380 99 123 45 67")
BUSINESS_SCHEDULE = os.getenv("BUSINESS_SCHEDULE", "Пн-Сб: 09:00 - 20:00, Вс: 10:00 - 18:00")

# Список предоставляемых услуг и цен
SERVICES = [
    ("💇 Стрижка", "500 грн"),
    ("💅 Маникюр", "700 грн"),
    ("💄 Макияж", "1000 грн"),
]
