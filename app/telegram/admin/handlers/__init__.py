from aiogram import Router
from telegram.admin.filters import admin
from . import panel, moderation, admins, support

def setup_admin_handlers() -> Router:
    router = Router()
    router.message.filter(admin.IsAdmin())
    router.callback_query.filter(admin.IsAdmin())
    
    router.include_router(panel.router)
    router.include_router(moderation.router)
    router.include_router(admins.router)
    router.include_router(support.router)
    
    return router
