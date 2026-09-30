import asyncio
import config

from store import Store

async def main():
    logger = config.logger
    
    logger.info("[main] Initialization started...")
    
    # store
    try:
        logger.info("[main] Initializing the database...")
        store = Store
        store.init_db()
        # from scripts import seed_test_data
        # seed_test_data.seed()
    except Exception as e:
        raise Exception(f"[main] Error initializing the database: {str(e)}") from e
    else:
        logger.info("[main] Database initialization completed")
        
    # bot
    try:
        logger.info("[main] bot initializing...")
        from telegram.bot import DatingBot
        bot = DatingBot()
    except Exception as e:
        raise Exception(f"[main] Error initializing bot: {str(e)}") from e
    else:
        logger.info("[main] bot initializing completed")
        
    logger.info("[main] Initialization completed")
    
    robokassa_runner = None
    try:
        from robokassa.server import start_result_server

        robokassa_runner = await start_result_server()
        logger.info("[main] Robokassa result server started")
    except Exception as e:
        logger.exception(f"[main] Robokassa result server failed to start: {e}")

    await bot.start()

    if robokassa_runner:
        await robokassa_runner.cleanup()
    
    logger.info("[main] END")
    
if __name__ == "__main__":
    asyncio.run(main())
