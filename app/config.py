import os, json

from setup_logger import setup_logger
logger = setup_logger("main")

BASE_PATH = os.environ.get("BASE_PATH", "./app/")
config_path = BASE_PATH+"config.json"

if not os.path.isfile(config_path): 
    raise FileNotFoundError("[config] File config.json not found")

try:
    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)  
        
    BOT_TOKEN = config['bot_token']
    LIST_ADMIN_USER_ID = config['list_admin_user_id']
    PAYMENT_PROVIDER = str(config.get("payment_provider", "yookassa")).strip().lower()
    YOOKASSA_PROVIDER_TOKEN = config.get("payment_provider_token", "")
    ROBOKASSA_PROVIDER_TOKEN = config.get("robokassa_provider_token", "")
    if PAYMENT_PROVIDER == "robokassa":
        PAYMENT_PROVIDER_TOKEN = ROBOKASSA_PROVIDER_TOKEN or YOOKASSA_PROVIDER_TOKEN
    else:
        PAYMENT_PROVIDER_TOKEN = YOOKASSA_PROVIDER_TOKEN
    ROBOKASSA_MERCHANT_LOGIN = config.get("robokassa_merchant_login", "")
    ROBOKASSA_PASSWORD_1 = config.get("robokassa_password_1", "")
    ROBOKASSA_PASSWORD_2 = config.get("robokassa_password_2", "")
    ROBOKASSA_IS_TEST = int(config.get("robokassa_is_test", 1))
    ROBOKASSA_PAYMENT_URL = config.get("robokassa_payment_url", "https://auth.robokassa.ru/Merchant/Index.aspx")
    ROBOKASSA_RESULT_HOST = config.get("robokassa_result_host", "0.0.0.0")
    ROBOKASSA_RESULT_PORT = int(config.get("robokassa_result_port", 8080))
    ROBOKASSA_RESULT_PATH = config.get("robokassa_result_path", "/robokassa/result")
    SUBSCRIPTION_PRICE_3_DAYS = config['subscription_price_3_days']
    SUBSCRIPTION_PRICE_7_DAYS = config['subscription_price_7_days']
    SUBSCRIPTION_PRICE_30_DAYS = config['subscription_price_30_days']
    ANONYMOUS_PROFILE_PRICE = config.get('anonymous_profile_price', 100000)
    NOMINATIM_USER_AGENT = config.get('nominatim_user_agent', 'TgDatingBot/1.0')
    FREE_VIEW_LIMIT = config.get('free_view_limit', 5)
    ELASTIC_URL = config['elastic_url']
    ELASTIC_INDEX = config['elastic_index']
    
    DB_PATH = BASE_PATH+config['db_path']
    
    DOWNLOADS_PATH = BASE_PATH+config['downloads_path']
    
except ValueError as e:
    raise ValueError(f"[config] Invalid config.json file format: {e}")
except Exception as e:
    raise Exception(f"[config] Error reading settings: {e}")
else:
    logger.info("[config] Reading settings completed")
