#!/usr/bin/env python3
"""
Verify that old symbols have no data points.
"""

from influxdb import InfluxDBClient
from config import get_config

config = get_config()
client = InfluxDBClient(
    host=config.get("INFLUXDB_HOST", "localhost"),
    port=config.get("INFLUXDB_PORT", 8086),
    username=config.get("INFLUXDB_USERNAME", None),
    password=config.get("INFLUXDB_PASSWORD", None),
    database=config.get("INFLUXDB_DATABASE", "market_data")
)

print("Checking old-format symbols for data...")
print("="*60)

old_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'BNBUSDT']

for symbol in old_symbols:
    query = f'SELECT COUNT(close) FROM "market_data" WHERE symbol = \'{symbol}\''
    result = client.query(query)
    points = list(result.get_points())
    
    if points and points[0].get('count', 0) > 0:
        print(f"❌ {symbol}: {points[0]['count']} points (NOT EMPTY!)")
    else:
        print(f"✓ {symbol}: 0 points (empty tag, no data)")

print("\n" + "="*60)
print("Checking new-format symbols...")
print("="*60)

new_symbols = ['BTCUSDT_BYBIT', 'BTC_DVOL', 'ETH_DVOL', 'ETHUSDT_BYBIT']

for symbol in new_symbols:
    query = f'SELECT COUNT(close) FROM "market_data" WHERE symbol = \'{symbol}\''
    result = client.query(query)
    points = list(result.get_points())
    
    if points and points[0].get('count', 0) > 0:
        print(f"✓ {symbol}: {points[0]['count']} points")
    else:
        print(f"❌ {symbol}: NO DATA!")

client.close()
