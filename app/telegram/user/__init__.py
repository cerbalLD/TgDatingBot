from aiogram import Router

from .handlers import start, profile, complaints, subscription, search, likes

def setup_user_handlers() -> Router:
    router = Router()
    
    router.include_router(start.router)
    router.include_router(profile.router)
    router.include_router(complaints.router)
    router.include_router(subscription.router)
    router.include_router(search.router)
    router.include_router(likes.router)
    
    return router
