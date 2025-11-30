import logging
import pandas as pd
from modules.bybit_klin import BybitKline
from modules.influx_writer import InfluxDBWriter
from config import get_config

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    config = get_config()
    influx_writer = InfluxDBWriter()
    bybit = BybitKline()

    with open("coins.txt", "r") as f:
        symbols = [line.strip() for line in f.readlines()]

    for symbol in symbols:
        try:
            # Fetch the last 2 hours to ensure we get the most recent closed candle
            df_kline = bybit.fetch_historical_kline(symbol, days=1, resolution=60) # 60 for 1 hour
            if not df_kline.empty:
                influx_writer.write_market_data(df_kline, "market_data", symbol, "Bybit", "kline")
                logging.info(f"Successfully fetched and stored data for {symbol}")
            else:
                logging.warning(f"No data returned for {symbol}")
        except Exception as e:
            logging.error(f"Failed to process {symbol}: {e}")

if __name__ == "__main__":
    logging.info("Starting data collection...")
    main()
    logging.info("Data collection finished.")
