# Quick Reference - Backfill System

## 1-Minute Quick Start

```bash
# Start backfill
cd /home/eulex/projects/laklak
python3 backfill.py

# Monitor progress
tail -f backfill.log
```

---

## Key Commands

### Start Backfill
```bash
python3 backfill.py
```

### Monitor in Real-time
```bash
tail -f backfill.log
```

### Check InfluxDB Connection
```bash
curl -I http://192.168.4.3:8086/ping
```

### Query Data in InfluxDB
```bash
python3 << 'EOF'
from influxdb import InfluxDBClient
client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')
result = client.query('SELECT COUNT(*) FROM "binance_ohlc"')
print(result)
EOF
```

---

## File Locations

| File | Purpose | Location |
|------|---------|----------|
| Main backfill | Start backfill | `backfill.py` |
| Asset list | Coins to backfill | `assets.txt` |
| Binance module | Fetch data | `modules/exchanges/binance.py` |
| InfluxDB writer | Write to DB | `modules/influx_writer.py` |
| Config | System settings | `config.py` |
| Log file | Progress log | `backfill.log` |

---

## Configuration Quick Edit

### Change Days to Backfill
Edit `backfill.py`:
```python
BACKFILL_CONFIG = {
    "TOTAL_DAYS": 30,  # Change from 90 to 30
}
```

### Change Resolution
Edit `backfill.py`:
```python
"BYBIT_RESOLUTION": "3600",  # 1-hour instead of 60 (1-minute)
```

### Change Batch Size
Edit `backfill.py`:
```python
"BATCH_SIZE": 1000,  # Increase from 500
```

---

## Database Info

**InfluxDB Server:** 192.168.4.3:8086  
**Database:** market_data  
**Measurement:** binance_ohlc  
**Tags:** symbol, exchange, timeframe  
**Fields:** open, high, low, close, volume  

---

## Asset Summary

- **Total Assets:** 547
- **Binance Coins:** 541 (BTCUSDT, ETHUSDT, etc.)
- **Yahoo Finance:** 6 (BTC=F, ETH=F, etc.)
- **Configured in:** assets.txt

---

## Performance Expectations

| Metric | Value |
|--------|-------|
| 90-day backfill | 5-10 minutes |
| With cooldowns | ~50 minutes |
| Per coin | 15-30 seconds |
| API usage | ~45% of limit |
| Rate limit | 1200 req/min |
| Cooldown | 10 min per 100 coins |

---

## Monitoring Tips

### What to Look For

**Success:** 
```
Processed 168 valid data points for BTCUSDT
Successfully wrote 5 points to InfluxDB
```

**Cooldown:**
```
⏸️ RATE LIMIT COOLDOWN: Processed 100 coins
Resume at: 2026-01-10 17:36:11
```

**Error:**
```
ERROR - Failed to fetch data for SYMBOL
```

### Stop Backfill
```bash
# Press Ctrl+C in terminal running backfill
# It will shutdown gracefully
```

### Resume Backfill
```bash
# Re-run backfill.py
# It will resume from where it left off
python3 backfill.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "assets.txt not found" | Run `python3 backfill.py` - it creates it |
| "Failed to connect to InfluxDB" | Check `192.168.4.3:8086` is running |
| HTTP 429 errors | Normal - wait for cooldown |
| No data written | Check `backfill.log` for errors |
| Slow performance | Increase `CHUNK_SIZE_DAYS` to reduce requests |

---

## Data Access

### Query Latest Price
```python
from influxdb import InfluxDBClient
client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')
result = client.query('SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT" ORDER BY time DESC LIMIT 1')
print(result)
```

### Export to CSV
```python
import pandas as pd
from influxdb import InfluxDBClient

client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')
result = client.query('SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT"')
df = pd.DataFrame(result.get_points())
df.to_csv('btcusdt_data.csv', index=False)
```

### Get Statistics
```python
from influxdb import InfluxDBClient
client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')

# Total records
result = client.query('SELECT COUNT(*) FROM "binance_ohlc"')
print(f"Total: {result}")

# Records per symbol (sample)
result = client.query('SELECT COUNT(*) FROM "binance_ohlc" GROUP BY symbol LIMIT 10')
print(f"By symbol: {result}")
```

---

## Common Code Snippets

### Fetch Single Coin
```python
from modules.exchanges.binance import BinanceFuturesKline

binance = BinanceFuturesKline()
df = binance.fetch_historical_kline('BTCUSDT', days=7, resolution='1h')
print(f"Fetched {len(df)} records")
```

### Fetch Multiple Coins
```python
coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
for coin in coins:
    df = binance.fetch_historical_kline(coin, days=7, resolution='1h')
    print(f"{coin}: {len(df)} records")
```

### Get Funding Rates
```python
df = binance.fetch_funding_rate('BTCUSDT', days=30)
print(f"Avg funding rate: {df['close'].mean():.6f}")
```

### Write to InfluxDB (Manual)
```python
from modules.influx_writer import InfluxDBWriter
from modules.exchanges.binance import BinanceFuturesKline

writer = InfluxDBWriter(host='192.168.4.3', database='market_data')
binance = BinanceFuturesKline()

df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')
writer.write_market_data(df, symbol='BTCUSDT', exchange='binance')
writer.flush()
writer.close()
```

---

## Environment Variables

Set before running (optional):

```bash
export BINANCE_API_URL="https://fapi.binance.com"
export INFLUXDB_HOST="192.168.4.3"
export INFLUXDB_PORT="8086"
export INFLUXDB_DATABASE="market_data"
```

---

## Backfill Flow

```
1. Load assets.txt (547 coins)
2. Connect to InfluxDB
3. For each coin:
   a. Fetch 90 days from Binance API
   b. Split into 0.7-day chunks
   c. Validate OHLC data
   d. Batch write to InfluxDB (500 records)
4. Every 100 coins: 10-minute cooldown
5. Final flush and close
```

---

## Log Levels

The backfill script logs:
- ✅ Success: "Successfully wrote X points"
- ⏸️ Pause: "RATE LIMIT COOLDOWN"
- ⚠️ Warning: "Skipped invalid row"
- ❌ Error: "Failed to fetch"
- ℹ️ Info: Progress updates

---

## Support Files

Located in `how_to/`:
- `BACKFILL_COMPLETE_GUIDE.md` - Full documentation
- `BINANCE_MODULE_COMPLETE.md` - Module reference
- `QUICK_REFERENCE.md` - This file
- `ASSETS_CONFIGURATION.md` - Asset setup
- `INFLUXDB_SETUP.md` - Database setup

---

**Need Help?** Check the complete guides or run:
```bash
python3 backfill.py --help
```
