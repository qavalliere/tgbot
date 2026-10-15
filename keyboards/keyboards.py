from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import config


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню бота.
    """
    keyboard = [
        [KeyboardButton(text="📋 Оставить заявку")],
        [KeyboardButton(text="💰 Услуги"), KeyboardButton(text="📍 Контакты")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_services_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура под списком услуг (быстрый переход к заявке или в меню).
    """
    keyboard = [
        [KeyboardButton(text="📋 Оставить заявку")],
        [KeyboardButton(text="◀️ В главное меню")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с одной кнопкой отмены (для шагов ввода имени и времени).
    """
    keyboard = [
        [KeyboardButton(text="❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для шага ввода телефона с кнопкой отправки контакта.
    """
    keyboard = [
        [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
        [KeyboardButton(text="❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Отправьте контакт или введите номер...",
    )


def get_services_choice_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для выбора услуги при оформлении заявки.
    Динамически формируется из списка config.SERVICES.
    """
    keyboard: list[list[KeyboardButton]] = []

    # Размещаем услуги по 2 кнопки в ряд
    row: list[KeyboardButton] = []
    for service_name, _ in config.SERVICES:
        row.append(KeyboardButton(text=service_name))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Дополнительные опции
    keyboard.append([KeyboardButton(text="Другая услуга")])
    keyboard.append([KeyboardButton(text="❌ Отменить")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите услугу из списка...",
    )


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для подтверждения или отмены заявки клиентом.
    """
    keyboard = [
        [KeyboardButton(text="✅ Отправить"), KeyboardButton(text="❌ Отменить")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Подтвердите отправку заявки...",
    )


def get_admin_decision_keyboard(lead_id: int | str) -> InlineKeyboardMarkup:
    """
    Инлайн-кнопки для владельца бизнеса (подтвердить или отклонить заявку).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_{lead_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{lead_id}"),
            ]
        ]
    )
