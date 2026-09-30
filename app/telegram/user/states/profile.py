from aiogram.fsm.state import StatesGroup, State

class ProfileStates(StatesGroup):
    """States для работы с профилем пользователя"""
    waiting_name = State()
    waiting_age = State()
    waiting_city = State()
    waiting_about = State()
    waiting_activity = State()
    waiting_partner = State()
    waiting_family = State()
    waiting_publish = State()
    waiting_photo = State()
    waiting_sex = State()
