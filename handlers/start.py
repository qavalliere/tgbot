from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.keyboards import get_main_keyboard

router = Router()


@router.message(CommandStart())
@router.message(F.text == "◀️ В главное меню")
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start и возврата в главное меню.
    Сбрасывает текущее состояние FSM, если оно было активно.
    """
    await state.clear()
    greeting_text = (
        "👋 Добро пожаловать!\n"
        "Мы готовы помочь вам.\n"
        "Выберите действие:"
    )
    await message.answer(
        text=greeting_text,
        reply_markup=get_main_keyboard(),
    )
