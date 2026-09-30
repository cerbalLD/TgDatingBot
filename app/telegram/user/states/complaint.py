from aiogram.fsm.state import StatesGroup, State


class ComplaintStates(StatesGroup):
    waiting_message = State()
