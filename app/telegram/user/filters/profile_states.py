from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram.user.states.profile import ProfileStates

class InAnyProfileState(Filter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current_state = await state.get_state()
        if not current_state:
            return False
        
        return current_state.startswith("ProfileStates:")