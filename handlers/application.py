import re
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import config
import database
from states.application import ApplicationState
from keyboards.keyboards import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_phone_keyboard,
    get_services_choice_keyboard,
    get_confirmation_keyboard,
    get_admin_decision_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()


def is_valid_phone(phone: str) -> bool:
    """
    Проверяет валидность введённого номера телефона.
    Должен содержать от 7 до 15 цифр и допустимые символы (+, -, скобки, пробелы).
    """
    clean_digits = re.sub(r"\D", "", phone)
    if not (7 <= len(clean_digits) <= 15):
        return False
    return bool(re.match(r"^\+?[0-9\s\-()]{7,25}$", phone.strip()))


# =====================================================================
# Отмена оформления заявки (доступна на любом шаге)
# =====================================================================
@router.message(Command("cancel"))
@router.message(F.text == "❌ Отменить")
async def cancel_handler(message: Message, state: FSMContext):
    """
    Отменяет текущее заполнение заявки, сбрасывает FSM
    и возвращает пользователя в главное меню.
    """
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        logger.info(f"Пользователь {message.from_user.id} отменил заполнение заявки.")

    await message.answer(
        text="❌ Оформление заявки отменено.\nВозвращаю вас в главное меню.",
        reply_markup=get_main_keyboard(),
    )


# =====================================================================
# Старт оформления заявки: Шаг 1 — Имя
# =====================================================================
@router.message(F.text == "📋 Оставить заявку")
@router.message(Command("apply"))
async def start_application(message: Message, state: FSMContext):
    """
    Запуск пошагового диалога оформления заявки.
    """
    await state.clear()
    await state.set_state(ApplicationState.name)

    await message.answer(
        text="Как вас зовут?",
        reply_markup=get_cancel_keyboard(),
    )


# =====================================================================
# Шаг 1 -> Шаг 2: Получение имени и запрос номера телефона
# =====================================================================
@router.message(ApplicationState.name, F.text)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Пожалуйста, введите ваше имя:")
        return

    await state.update_data(name=name)
    await state.set_state(ApplicationState.phone)

    await message.answer(
        text="Введите номер телефона.",
        reply_markup=get_phone_keyboard(),
    )


# =====================================================================
# Шаг 2 -> Шаг 3: Получение номера телефона и выбор услуги
# =====================================================================
@router.message(ApplicationState.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """
    Обработка номера телефона, переданного через кнопку 'Поделиться контактом'.
    """
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await state.set_state(ApplicationState.service)

    await message.answer(
        text="Какая услуга вас интересует?",
        reply_markup=get_services_choice_keyboard(),
    )


@router.message(ApplicationState.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    """
    Обработка номера телефона, введённого текстом с валидацией.
    """
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer(
            text="❌ Некорректный номер телефона.\n"
                 "Пожалуйста, введите корректный номер (например: +380991234567) "
                 "или воспользуйтесь кнопкой «📱 Поделиться контактом».",
            reply_markup=get_phone_keyboard(),
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(ApplicationState.service)

    await message.answer(
        text="Какая услуга вас интересует?",
        reply_markup=get_services_choice_keyboard(),
    )


@router.message(ApplicationState.phone)
async def process_phone_invalid(message: Message):
    await message.answer(
        text="Пожалуйста, введите номер телефона сообщением или нажмите кнопку «📱 Поделиться контактом».",
        reply_markup=get_phone_keyboard(),
    )


# =====================================================================
# Шаг 3 -> Шаг 4: Выбор услуги и запрос даты/времени
# =====================================================================
@router.message(ApplicationState.service, F.text)
async def process_service(message: Message, state: FSMContext):
    service = message.text.strip()
    await state.update_data(service=service)
    await state.set_state(ApplicationState.time)

    await message.answer(
        text="Когда вам удобно прийти?",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ApplicationState.service)
async def process_service_invalid(message: Message):
    await message.answer(
        text="Пожалуйста, выберите услугу из предложенных кнопок или напишите её текстом.",
        reply_markup=get_services_choice_keyboard(),
    )


# =====================================================================
# Шаг 4 -> Шаг 5: Желаемое время и показ итоговой заявки
# =====================================================================
@router.message(ApplicationState.time, F.text)
async def process_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    await state.update_data(time=time_str)
    await state.set_state(ApplicationState.confirmation)

    data = await state.get_data()
    summary_text = (
        "Проверьте данные:\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📞 Телефон: {data.get('phone')}\n"
        f"💇 Услуга: {data.get('service')}\n"
        f"🕐 Время: {data.get('time')}\n\n"
        "Всё верно?"
    )

    await message.answer(
        text=summary_text,
        reply_markup=get_confirmation_keyboard(),
    )


@router.message(ApplicationState.time)
async def process_time_invalid(message: Message):
    await message.answer(
        text="Пожалуйста, укажите удобное для вас время текстом (например: завтра в 15:00):",
        reply_markup=get_cancel_keyboard(),
    )


# =====================================================================
# Шаг 5: Подтверждение и отправка заявки владельцу с сохранением в БД
# =====================================================================
@router.message(ApplicationState.confirmation, F.text == "✅ Отправить")
async def process_confirmation_send(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "Не указано")
    phone = data.get("phone", "Не указано")
    service = data.get("service", "Не указано")
    time_val = data.get("time", "Не указано")
    username = message.from_user.username

    # Сохраняем заявку в базу данных SQLite
    try:
        lead_id = await database.create_lead(
            client_chat_id=message.chat.id,
            client_username=username,
            name=name,
            phone=phone,
            service=service,
            desired_time=time_val,
        )
    except Exception as exc:
        logger.exception(f"Ошибка сохранения заявки в базу данных: {exc}")
        await message.answer(
            "Произошла внутренняя ошибка при сохранении заявки. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard(),
        )
        await state.clear()
        return

    # Текст сообщения для владельцев/администраторов бизнеса
    username_str = f"@{username}" if username else "скрыт"
    admin_notification = (
        f"🔔 НОВАЯ ЗАЯВКА #{lead_id}\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"💇 Услуга: {service}\n"
        f"🕐 Желаемое время: {time_val}\n"
        f"💬 Профиль: {username_str}\n\n"
        f"Источник: Telegram"
    )

    # Отправляем уведомление всем администраторам
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                reply_markup=get_admin_decision_keyboard(lead_id),
            )
            logger.info(
                f"Заявка #{lead_id} от пользователя {message.from_user.id} "
                f"успешно отправлена администратору {admin_id}."
            )
        except Exception as exc:
            logger.error(f"Не удалось отправить заявку администратору {admin_id}: {exc}")

    # Очищаем состояние пользователя
    await state.clear()

    # Сообщение клиенту об успешном принятии заявки
    success_text = (
        "✅ Спасибо! Ваша заявка принята.\n"
        "Владелец свяжется с вами или подтвердит время прямо здесь."
    )
    await message.answer(
        text=success_text,
        reply_markup=get_main_keyboard(),
    )


@router.message(ApplicationState.confirmation)
async def process_confirmation_other(message: Message):
    await message.answer(
        text="Пожалуйста, нажмите «✅ Отправить» для отправки заявки или «❌ Отменить» для отмены.",
        reply_markup=get_confirmation_keyboard(),
    )


# =====================================================================
# Обработка действий администратора (Подтвердить / Отклонить)
# =====================================================================
@router.callback_query(F.data.startswith("approve_"))
async def process_admin_approve(callback: CallbackQuery):
    # Проверка прав администратора
    if not config.is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет прав администратора.", show_alert=True)
        return

    try:
        lead_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("⚠️ Неверный идентификатор заявки.", show_alert=True)
        return

    lead = await database.get_lead(lead_id)
    if not lead:
        await callback.answer("⚠️ Данные заявки не найдены.", show_alert=True)
        return

    if lead["status"] != "pending":
        status_label = "подтверждена" if lead["status"] == "approved" else "отклонена"
        await callback.answer(f"Заявка #{lead_id} уже была {status_label}.", show_alert=True)
        return

    # Обновляем статус в базе данных
    updated = await database.update_lead_status(lead_id, "approved")
    if not updated:
        await callback.answer(f"Заявка #{lead_id} уже была обработана.", show_alert=True)
        return

    # Редактируем сообщение у админа: убираем кнопки и меняем статус
    admin_name = callback.from_user.full_name
    updated_text = (
        f"🔔 ЗАЯВКА #{lead_id} — ✅ ПОДТВЕРЖДЕНА\n\n"
        f"👤 Имя: {lead['name']}\n"
        f"📞 Телефон: {lead['phone']}\n"
        f"💇 Услуга: {lead['service']}\n"
        f"🕐 Время: {lead['desired_time']}\n\n"
        f"Статус: ✅ Подтверждено администратором ({admin_name})"
    )
    await callback.message.edit_text(updated_text)
    await callback.answer(f"Заявка #{lead_id} подтверждена! Клиент уведомлен.")

    # Отправляем уведомление клиенту
    try:
        client_text = (
            f"🎉 Отличные новости! Ваша заявка #{lead_id} подтверждена!\n\n"
            f"💇 Услуга: {lead['service']}\n"
            f"🕐 Ждём вас: {lead['desired_time']}\n"
            f"🏢 Адрес: {config.BUSINESS_ADDRESS}\n"
            f"📞 Телефон для связи: {config.BUSINESS_PHONE}"
        )
        await callback.bot.send_message(
            chat_id=lead["client_chat_id"],
            text=client_text,
        )
    except Exception as exc:
        logger.error(f"Не удалось отправить уведомление клиенту {lead['client_chat_id']}: {exc}")


@router.callback_query(F.data.startswith("reject_"))
async def process_admin_reject(callback: CallbackQuery):
    # Проверка прав администратора
    if not config.is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет прав администратора.", show_alert=True)
        return

    try:
        lead_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("⚠️ Неверный идентификатор заявки.", show_alert=True)
        return

    lead = await database.get_lead(lead_id)
    if not lead:
        await callback.answer("⚠️ Данные заявки не найдены.", show_alert=True)
        return

    if lead["status"] != "pending":
        status_label = "подтверждена" if lead["status"] == "approved" else "отклонена"
        await callback.answer(f"Заявка #{lead_id} уже была {status_label}.", show_alert=True)
        return

    # Обновляем статус в базе данных
    updated = await database.update_lead_status(lead_id, "rejected")
    if not updated:
        await callback.answer(f"Заявка #{lead_id} уже была обработана.", show_alert=True)
        return

    # Редактируем сообщение у админа
    admin_name = callback.from_user.full_name
    updated_text = (
        f"🔔 ЗАЯВКА #{lead_id} — ❌ ОТКЛОНЕНА\n\n"
        f"👤 Имя: {lead['name']}\n"
        f"📞 Телефон: {lead['phone']}\n"
        f"💇 Услуга: {lead['service']}\n"
        f"🕐 Время: {lead['desired_time']}\n\n"
        f"Статус: ❌ Отклонено администратором ({admin_name})"
    )
    await callback.message.edit_text(updated_text)
    await callback.answer(f"Заявка #{lead_id} отклонена. Клиент уведомлен.")

    # Отправляем уведомление клиенту
    try:
        client_text = (
            f"Здравствуйте! К сожалению, мы не можем принять вашу заявку #{lead_id} на {lead['desired_time']} "
            f"(время занято или мастер недоступен).\n\n"
            f"Пожалуйста, выберите другое удобное время в меню «📋 Оставить заявку» "
            f"или свяжитесь с нами: {config.BUSINESS_PHONE}."
        )
        await callback.bot.send_message(
            chat_id=lead["client_chat_id"],
            text=client_text,
        )
    except Exception as exc:
        logger.error(f"Не удалось отправить уведомление клиенту {lead['client_chat_id']}: {exc}")
