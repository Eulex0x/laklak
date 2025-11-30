import requests
import pandas as pd 
import logging
from config import get_config
from modules.bybit_klin import BybitKline
from modules.deribit_dvol import DeribitDVOL
config = get_config()

def iv_data():
    logging.info("Fetches Implied Volatility (IV) data from Bybit API and returns it as a pandas DataFrame.")
    # using Derbibit DVOL as a proxy for IV
    deribit = DeribitDVOL()
    df_iv = deribit.fetch_historical_dvol(currency=config['BASE_COIN'], days=config['DAYS'], resolution=config['RESOLUTION_IV'])
    bybit = BybitKline()
    df_kline = bybit.fetch_historical_kline(currency=config['BASE_COIN'], days=config['DAYS'], resolution=config['RESOLUTION_KLINE'])
    return df_iv, df_kline