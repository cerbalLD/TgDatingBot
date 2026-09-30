from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from telegram.user import setup_user_handlers
from telegram.admin.handlers import setup_admin_handlers
from telegram.middlewares.logging import UserActionLoggingMiddleware

class DatingBot():
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.message.middleware(UserActionLoggingMiddleware())
        self.dp.callback_query.middleware(UserActionLoggingMiddleware())
        
        # Регистрируем пользовательские хендлеры
        user_router = setup_user_handlers()
        self.dp.include_router(user_router)
        
        # Регистрируем админские хендлеры (с фильтром)
        admin_router = setup_admin_handlers()
        self.dp.include_router(admin_router)
        
    async def start(self):
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        await self.dp.stop_polling(self.bot)
