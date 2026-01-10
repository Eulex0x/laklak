# InfluxDB Setup & Configuration

## Overview

This guide covers InfluxDB setup, configuration, and data verification for the backfill system.

**Version:** InfluxDB 1.6+  
**Database:** market_data  
**Location:** 192.168.4.3:8086

---

## Quick Setup

### 1. Verify InfluxDB is Running

```bash
# Check if InfluxDB responds
curl -I http://192.168.4.3:8086/ping

# Expected response:
# HTTP/1.1 204 No Content
# X-Influxdb-Version: 1.8.x
```

### 2. Create Database

```bash
# Create market_data database
curl -X POST http://192.168.4.3:8086/query --data-urlencode "q=CREATE DATABASE market_data"

# Verify it exists
curl -s http://192.168.4.3:8086/query?q=SHOW%20DATABASES
```

### 3. Verify Python Connection

```python
from influxdb import InfluxDBClient

client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')
print(f"Connected: {client.ping()}")
```

---

## Configuration Files

### File: `config.py`

```python
SETTINGS = {
    # InfluxDB Configuration
    "INFLUXDB_HOST": "192.168.4.3",
    "INFLUXDB_PORT": 8086,
    "INFLUXDB_DATABASE": "market_data",
    "INFLUXDB_USERNAME": None,          # Optional
    "INFLUXDB_PASSWORD": None,          # Optional
    "INFLUXDB_BATCH_SIZE": 2,           # Records per write
}
```

### Environment Variables (Optional)

```bash
export INFLUXDB_HOST=192.168.4.3
export INFLUXDB_PORT=8086
export INFLUXDB_DATABASE=market_data
export INFLUXDB_USERNAME=your_username
export INFLUXDB_PASSWORD=your_password
```

---

## Data Schema

### Measurement: `binance_ohlc`

```
binance_ohlc
├── Tags (indexed for fast queries)
│   ├── symbol: BTCUSDT, ETHUSDT, etc.
│   ├── exchange: binance
│   └── timeframe: 1m, 5m, 1h, 4h, 1d
│
├── Fields (values stored)
│   ├── open (float)
│   ├── high (float)
│   ├── low (float)
│   ├── close (float)
│   └── volume (float)
│
└── Time (UTC, nanosecond precision)
```

### Example Data Point

```json
{
  "measurement": "binance_ohlc",
  "tags": {
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "timeframe": "1m"
  },
  "fields": {
    "open": 90000.00,
    "high": 90500.00,
    "low": 89900.00,
    "close": 90300.00,
    "volume": 12345.67
  },
  "timestamp": 1704307200000000000
}
```

---

## Writing Data

### Using InfluxDBWriter Class

```python
from modules.influx_writer import InfluxDBWriter
from modules.exchanges.binance import BinanceFuturesKline

# Initialize writer
writer = InfluxDBWriter(
    host='192.168.4.3',
    port=8086,
    database='market_data',
    batch_size=500
)

# Fetch data
binance = BinanceFuturesKline()
df = binance.fetch_historical_kline('BTCUSDT', days=7, resolution='1h')

# Write to database
writer.write_market_data(
    df=df,
    symbol='BTCUSDT',
    exchange='binance',
    data_type='kline',
    period='1h'
)

# Flush remaining data
writer.flush()
writer.close()
```

### Manual Write (InfluxDB API)

```python
from influxdb import InfluxDBClient
from datetime import datetime, timezone

client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')

# Prepare data point
point = {
    "measurement": "binance_ohlc",
    "tags": {
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "timeframe": "1h"
    },
    "time": datetime.now(timezone.utc),
    "fields": {
        "open": 90000.00,
        "high": 90500.00,
        "low": 89900.00,
        "close": 90300.00,
        "volume": 12345.67
    }
}

# Write
client.write_points([point])
```

---

## Querying Data

### Basic Query

```python
from influxdb import InfluxDBClient

client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')

# Get latest record
result = client.query('SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT" ORDER BY time DESC LIMIT 1')
print(result)
```

### Query Examples

#### 1. Get All Records for a Symbol

```bash
curl -G 'http://192.168.4.3:8086/query' \
  --data-urlencode 'db=market_data' \
  --data-urlencode 'q=SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT"'
```

#### 2. Count Records by Symbol

```python
result = client.query('SELECT COUNT(*) FROM "binance_ohlc" GROUP BY symbol')
for series in result:
    symbol = series['tags']['symbol']
    count = series['points'][0]['count']
    print(f"{symbol}: {count}")
```

#### 3. Get Price Range

```python
result = client.query('SELECT MIN(low), MAX(high) FROM "binance_ohlc" WHERE symbol="BTCUSDT"')
for point in result.get_points():
    print(f"Min: {point['min']}, Max: {point['max']}")
```

#### 4. Get Latest 100 Records

```python
result = client.query('SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT" ORDER BY time DESC LIMIT 100')
df = pd.DataFrame(result.get_points())
```

#### 5. Calculate Moving Average

```python
result = client.query('SELECT MEAN(close) FROM "binance_ohlc" WHERE symbol="BTCUSDT" GROUP BY time(1h)')
```

#### 6. Date Range Query

```python
result = client.query(
    'SELECT * FROM "binance_ohlc" '
    'WHERE symbol="BTCUSDT" AND time > 2026-01-01 AND time < 2026-01-31'
)
```

---

## Data Verification

### Check Connection

```python
from influxdb import InfluxDBClient

client = InfluxDBClient(host='192.168.4.3', port=8086, database='market_data')
print(client.ping())  # Should return True
```

### Check Database Exists

```python
databases = client.get_list_database()
print([db['name'] for db in databases])
# Should include 'market_data'
```

### Check Data Was Written

```python
# Count total records
result = client.query('SELECT COUNT(*) FROM "binance_ohlc"')
for point in result.get_points():
    print(f"Total records: {point['count']}")

# Count by symbol
result = client.query('SELECT COUNT(*) FROM "binance_ohlc" GROUP BY symbol')
print(f"Symbols: {len(result)}")
```

### Verify Data Quality

```python
import pandas as pd

# Get sample data
result = client.query('SELECT * FROM "binance_ohlc" WHERE symbol="BTCUSDT" LIMIT 100')
df = pd.DataFrame(result.get_points())

# Check OHLC logic
assert (df['high'] >= df['low']).all()
assert (df['high'] >= df['open']).all()
assert (df['high'] >= df['close']).all()
assert (df['low'] <= df['open']).all()
assert (df['low'] <= df['close']).all()

# Check for gaps
print(f"Records: {len(df)}")
print(f"Time range: {df['time'].min()} to {df['time'].max()}")
print("✅ Data quality verified")
```

---

## Common Operations

### Drop Measurement

```bash
# WARNING: This deletes all data in the measurement!
curl -X POST http://192.168.4.3:8086/query \
  --data-urlencode 'db=market_data' \
  --data-urlencode 'q=DROP MEASUREMENT "binance_ohlc"'
```

### Drop Database

```bash
# WARNING: This deletes the entire database!
curl -X POST http://192.168.4.3:8086/query \
  --data-urlencode 'q=DROP DATABASE "market_data"'
```

### Delete Specific Symbol

```python
client.query('DELETE FROM "binance_ohlc" WHERE symbol="BTCUSDT"')
```

### Delete Old Data

```python
# Keep only last 30 days
client.query('DELETE FROM "binance_ohlc" WHERE time < now() - 30d')
```

---

## Retention Policies

### Create Retention Policy

```python
# Keep data for 90 days
client.create_retention_policy('90d', '90d', 1, 'binance_ohlc')

# Keep data forever
client.create_retention_policy('forever', 'INF', 1, 'binance_ohlc')
```

### List Retention Policies

```python
policies = client.get_list_retention_policies('market_data')
print(policies)
```

### Modify Retention Policy

```python
client.alter_retention_policy('90d', 'market_data', '180d', 1)
```

---

## Performance Optimization

### Add Indexes

```python
# Tags are indexed by default
# No need for additional indexes on measurements
```

### Optimize Storage

1. **Batch Writes:** Write multiple records at once
   ```python
   points = [...]  # list of 100+ points
   client.write_points(points)
   ```

2. **Continuous Aggregates:** Pre-calculate sums/averages
   ```python
   # InfluxDB Enterprise feature
   ```

3. **Data Compression:** InfluxDB 1.6+ compresses by default

### Monitor Storage

```bash
# Check disk usage
du -sh /var/lib/influxdb/

# Check database size (InfluxDB API)
curl -G 'http://192.168.4.3:8086/query' \
  --data-urlencode 'db=market_data' \
  --data-urlencode 'q=SHOW STATS'
```

---

## Backup & Restore

### Backup Database

```bash
# Backup using influxd backup command
influxd backup -database market_data /path/to/backup

# Or use Python client
# No direct backup method - use command line
```

### Restore Database

```bash
# Restore using influxd restore command
influxd restore -database market_data -newdb market_data_restore /path/to/backup
```

---

## Troubleshooting

### Problem: Connection Refused

```
Error: Failed to connect to InfluxDB at 192.168.4.3:8086
```

**Solution:**
1. Check InfluxDB is running: `systemctl status influxdb`
2. Check port: `netstat -tuln | grep 8086`
3. Check firewall: `ufw allow 8086`

### Problem: Database Not Found

```
Error: database not found
```

**Solution:**
```bash
curl -X POST http://192.168.4.3:8086/query --data-urlencode "q=CREATE DATABASE market_data"
```

### Problem: Write Failed

```
Error: write failed: unable to parse request
```

**Solution:**
- Check data format is valid JSON
- Check timestamp is in nanoseconds
- Check field values are numbers

### Problem: Query Returns Empty

```python
result = client.query('SELECT * FROM "binance_ohlc"')
print(result)  # ResultSet({})
```

**Solution:**
1. Check data exists: `SELECT COUNT(*) FROM "binance_ohlc"`
2. Check time range: Ensure time filter is correct
3. Check symbols: `SELECT DISTINCT symbol FROM "binance_ohlc"`

---

## Advanced Configuration

### Enable Authentication

```python
# In config.py
"INFLUXDB_USERNAME": "admin",
"INFLUXDB_PASSWORD": "secure_password"
```

```python
# Connect with auth
client = InfluxDBClient(
    host='192.168.4.3',
    port=8086,
    username='admin',
    password='secure_password',
    database='market_data'
)
```

### Configure Log Retention

In `/etc/influxdb/influxdb.conf`:
```ini
[retention]
  enabled = true
  check-interval = "30m"

[continuous_queries]
  enabled = true
```

### Set Memory Limits

In `/etc/influxdb/influxdb.conf`:
```ini
[coordinator]
  max-select-point = 0  # No limit
  max-select-series = 0  # No limit
  max-select-buckets = 0  # No limit
```

---

## Summary

✅ InfluxDB configured at 192.168.4.3:8086  
✅ Database: market_data  
✅ Measurement: binance_ohlc  
✅ Data schema optimized for time-series  
✅ Batch writing enabled  
✅ Production ready

**Next Step:** Start backfill with `python3 backfill.py`
