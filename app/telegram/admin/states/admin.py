from aiogram.fsm.state import StatesGroup, State


class AdminManageStates(StatesGroup):
    waiting_add_contact = State()
    waiting_remove_contact = State()


class AdminModerationStates(StatesGroup):
    waiting_reject_reason = State()


class AdminComplaintStates(StatesGroup):
    waiting_ban_message = State()


class AdminBroadcastStates(StatesGroup):
    waiting_message = State()
