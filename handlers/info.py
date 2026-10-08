from aiogram import Router, F
from aiogram.types import Message

import config
from keyboards.keyboards import get_main_keyboard, get_services_keyboard

router = Router()


@router.message(F.text == "💰 Услуги")
async def show_services(message: Message):
    """
    Показывает список услуг и цен, а также кнопку перехода к оформлению заявки.
    """
    lines = [f"{name} — {price}" for name, price in config.SERVICES]
    services_text = "\n".join(lines)

    await message.answer(
        text=services_text,
        reply_markup=get_services_keyboard(),
    )


@router.message(F.text == "📍 Контакты")
async def show_contacts(message: Message):
    """
    Показывает контактную информацию бизнеса.
    Значения берутся из config.py.
    """
    contacts_text = (
        "📍 Контакты:\n\n"
        f"🏢 Адрес: {config.BUSINESS_ADDRESS}\n"
        f"📞 Телефон: {config.BUSINESS_PHONE}\n"
        f"🕐 График работы: {config.BUSINESS_SCHEDULE}"
    )

    await message.answer(
        text=contacts_text,
        reply_markup=get_main_keyboard(),
    )
