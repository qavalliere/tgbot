from aiogram.fsm.state import State, StatesGroup


class ApplicationState(StatesGroup):
    """
    Машина состояний (FSM) для пошагового оформления заявки клиентом.
    """
    name = State()          # Шаг 1: ввод имени
    phone = State()         # Шаг 2: ввод или передача номера телефона
    service = State()       # Шаг 3: выбор услуги
    time = State()          # Шаг 4: желаемая дата/время
    confirmation = State()  # Шаг 5: проверка и подтверждение заявки
