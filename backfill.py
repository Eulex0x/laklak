import logging
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
            # Fetch the last 365 days of 1-hour data
            df_kline = bybit.fetch_historical_kline(symbol, days=365, resolution=60)
            if not df_kline.empty:
                influx_writer.write_market_data(df_kline, "market_data", symbol, "Bybit", "kline")
                logging.info(f"Successfully backfilled data for {symbol}")
            else:
                logging.warning(f"No historical data returned for {symbol}")
        except Exception as e:
            logging.error(f"Failed to backfill {symbol}: {e}")

if __name__ == "__main__":
    logging.info("Starting historical data backfill...")
    main()
    logging.info("Historical data backfill finished.")
