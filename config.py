from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_COIN = os.getenv("BASE_COIN", "BTC")
DAYS = int(os.getenv("DAYS", 10))
RESOLUTION_KLINE = os.getenv("RESOLUTION_KLINE")
RESOLUTION_IV = os.getenv("RESOLUTION_IV")
IV_AVERAGE_PERIOD = int(os.getenv("IV_AVERAGE_PERIOD", 5))


def get_config():
    return {
        "API_KEY": API_KEY,
        "API_SECRET": API_SECRET,
        "BASE_COIN": BASE_COIN,
        "DAYS": DAYS,
        "RESOLUTION_KLINE": int(RESOLUTION_KLINE),
        "RESOLUTION_IV": int(RESOLUTION_IV) * 60,
        "IV_AVERAGE_PERIOD": IV_AVERAGE_PERIOD
    }  