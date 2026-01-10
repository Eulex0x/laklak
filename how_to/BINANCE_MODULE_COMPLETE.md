# Binance Futures Module - Technical Reference

## Overview

The `BinanceFuturesKline` class provides a complete interface for fetching OHLCV (Open, High, Low, Close, Volume) data and funding rates from Binance Futures.

**Module:** `modules/exchanges/binance.py`  
**API:** Binance Futures (https://fapi.binance.com)  
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Class Overview](#class-overview)
2. [Methods](#methods)
3. [Usage Examples](#usage-examples)
4. [Supported Timeframes](#supported-timeframes)
5. [API Details](#api-details)
6. [Error Handling](#error-handling)
7. [Performance Tips](#performance-tips)

---

## Class Overview

```python
class BinanceFuturesKline:
    """
    Binance Futures exchange API integration for fetching OHLC data.
    
    Binance Futures API: https://fapi.binance.com
    """
    BASE_URL = "https://fapi.binance.com"
```

### Key Features

- **OHLCV Data Fetching:** Historical candlestick data
- **Funding Rate Support:** 8-hour funding rate history
- **Multi-Timeframe:** 1m to 1M (monthly) candles
- **Batch Processing:** Handles 1500 candles per request
- **Error Handling:** Graceful failures and validation
- **Rate Limit Aware:** Respects API limits (1200 req/min)

---

## Methods

### 1. `fetch_historical_kline()`

Fetch historical OHLCV data from Binance Futures.

```python
@staticmethod
def fetch_historical_kline(
    symbol: str,
    days: int,
    resolution: int | str = 60,
    start_time=None,
    end_time=None
) -> pd.DataFrame
```

**Parameters:**
- `symbol` (str): Trading pair (e.g., "BTCUSDT", "ETHUSDT")
- `days` (int): Number of days to fetch (used if start_time not provided)
- `resolution` (int | str): Time resolution
  - Integer minutes: 60, 240, 1440, etc.
  - Interval strings: "1m", "5m", "1h", "4h", "1d", etc.
- `start_time` (int, optional): Start timestamp in milliseconds
- `end_time` (int, optional): End timestamp in milliseconds

**Returns:**
```python
pd.DataFrame: Columns ['time', 'open', 'high', 'low', 'close', 'volume']
  - time: datetime (UTC)
  - open: float (opening price)
  - high: float (highest price)
  - low: float (lowest price)
  - close: float (closing price)
  - volume: float (trading volume)
```

**Example:**

```python
from modules.exchanges.binance import BinanceFuturesKline

binance = BinanceFuturesKline()

# Fetch 7 days of 1-hour data
df = binance.fetch_historical_kline('BTCUSDT', days=7, resolution='1h')

print(f"Fetched {len(df)} records")
print(df.head())
#                      time       open       high        low      close         volume
# 0 2026-01-03 17:00:00+00:00  90000.00  90500.00  89900.00  90300.00  12345.67
# 1 2026-01-03 18:00:00+00:00  90300.00  91000.00  90200.00  90800.00  15432.10
```

---

### 2. `fetch_funding_rate()`

Fetch funding rate history for a perpetual contract.

```python
@staticmethod
def fetch_funding_rate(
    symbol: str,
    days: int = 1
) -> pd.DataFrame
```

**Parameters:**
- `symbol` (str): Trading pair (e.g., "BTCUSDT")
- `days` (int): Number of days of history to fetch (default: 1)

**Returns:**
```python
pd.DataFrame: Columns ['time', 'open', 'high', 'low', 'close', 'volume']
  - time: datetime (UTC)
  - open/high/low/close: float (funding rate - all the same value)
  - volume: float (0, N/A for funding rates)
```

**Example:**

```python
# Fetch 30 days of funding rates
df = binance.fetch_funding_rate('BTCUSDT', days=30)

print(f"Fetched {len(df)} funding rate records")
print(df[['time', 'close']].head())
#                      time      close
# 0 2025-12-12 00:00:00+00:00  0.0000765
# 1 2025-12-12 08:00:00+00:00  0.0000891
# 2 2025-12-12 16:00:00+00:00  0.0001000
```

**Funding Rate Period:** Binance uses fixed 8-hour periods (3x daily)

---

### 3. `fetch_funding_rate_period()`

Get funding rate settlement period metadata.

```python
@staticmethod
def fetch_funding_rate_period(symbol: str) -> dict
```

**Parameters:**
- `symbol` (str): Trading pair (e.g., "BTCUSDT")

**Returns:**
```python
dict: {
    'symbol': str,                    # e.g., "BTCUSDT"
    'fundingInterval': int,           # Hours (8 for Binance)
    'fundingIntervalMinutes': int,    # Minutes (480 for Binance)
    'timestamp': int,                 # Fetch timestamp (ms)
    'method': str,                    # 'constant' for Binance
    'note': str                       # Description
}
```

**Example:**

```python
info = binance.fetch_funding_rate_period('BTCUSDT')

print(f"Funding interval: {info['fundingInterval']} hours")
print(f"Funding times: 00:00, 08:00, 16:00 UTC")
# Output: Funding interval: 8 hours
```

---

## Usage Examples

### Example 1: Simple OHLC Fetch

```python
from modules.exchanges.binance import BinanceFuturesKline
import pandas as pd

binance = BinanceFuturesKline()

# Fetch 3 days of 1-hour data
df = binance.fetch_historical_kline('BTCUSDT', days=3, resolution='1h')

print(f"Symbol: BTCUSDT")
print(f"Records: {len(df)}")
print(f"Time Range: {df['time'].min()} to {df['time'].max()}")
print(f"\nFirst record:")
print(df.iloc[0])
```

### Example 2: Multiple Coins

```python
coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']

for coin in coins:
    df = binance.fetch_historical_kline(coin, days=7, resolution='1h')
    print(f"{coin}: {len(df)} records")
    if not df.empty:
        print(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
```

### Example 3: Different Timeframes

```python
# 1-minute data
df_1m = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1m')
print(f"1m data: {len(df_1m)} records")  # ~1440 records

# 5-minute data
df_5m = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='5m')
print(f"5m data: {len(df_5m)} records")  # ~288 records

# 1-hour data
df_1h = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')
print(f"1h data: {len(df_1h)} records")  # ~24 records

# 1-day data
df_1d = binance.fetch_historical_kline('BTCUSDT', days=90, resolution='1d')
print(f"1d data: {len(df_1d)} records")  # ~90 records
```

### Example 4: Specific Date Range

```python
from datetime import datetime, timezone

# Define date range
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
end = datetime(2025, 12, 31, tzinfo=timezone.utc)

start_ms = int(start.timestamp() * 1000)
end_ms = int(end.timestamp() * 1000)

# Fetch for specific range
df = binance.fetch_historical_kline(
    'BTCUSDT',
    days=1,  # Ignored if start_time provided
    resolution='1d',
    start_time=start_ms,
    end_time=end_ms
)

print(f"Data from {df['time'].min()} to {df['time'].max()}")
```

### Example 5: Funding Rate Tracking

```python
# Track funding rates over time
df = binance.fetch_funding_rate('BTCUSDT', days=90)

print(f"Funding rate statistics (90 days):")
print(f"  Average: {df['close'].mean():.6f}")
print(f"  Min: {df['close'].min():.6f}")
print(f"  Max: {df['close'].max():.6f}")
print(f"  Std Dev: {df['close'].std():.6f}")
```

### Example 6: Data Validation

```python
df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')

# Validate OHLC logic
assert (df['high'] >= df['low']).all(), "High must be >= Low"
assert (df['high'] >= df['open']).all(), "High must be >= Open"
assert (df['high'] >= df['close']).all(), "High must be >= Close"
assert (df['low'] <= df['open']).all(), "Low must be <= Open"
assert (df['low'] <= df['close']).all(), "Low must be <= Close"

# Check for gaps in data
time_diff = df['time'].diff()
gaps = time_diff[time_diff > pd.Timedelta('1h5m')]
if not gaps.empty:
    print(f"Warning: Found {len(gaps)} data gaps")

print("✅ Data validation passed")
```

---

## Supported Timeframes

### Interval Mapping

The module supports multiple resolution formats:

| Format | Interval | Period |
|--------|----------|--------|
| "1m" / 1 | 1-minute | 1 min |
| "3m" / 3 | 3-minute | 3 min |
| "5m" / 5 | 5-minute | 5 min |
| "15m" / 15 | 15-minute | 15 min |
| "30m" / 30 | 30-minute | 30 min |
| "1h" / 60 | 1-hour | 1 hour |
| "2h" / 120 | 2-hour | 2 hours |
| "4h" / 240 | 4-hour | 4 hours |
| "6h" / 360 | 6-hour | 6 hours |
| "8h" / 480 | 8-hour | 8 hours |
| "12h" / 720 | 12-hour | 12 hours |
| "1d" / 1440 | 1-day | 1 day |
| "3d" | 3-day | 3 days |
| "1w" | 1-week | 7 days |
| "1M" | 1-month | ~30 days |

### Data Point Limits

Binance API limits responses to 1500 candles per request. The module automatically:
- Splits large requests into 0.7-day chunks
- Fetches in batches
- Combines results

**Effective limits:**
- 1-minute data: ~1500 minutes (25 hours)
- 1-hour data: ~1500 hours (62.5 days)
- 1-day data: ~1500 days (4+ years)

---

## API Details

### Binance Futures API

**Endpoint:** `https://fapi.binance.com`

**Klines Endpoint:**
```
GET /fapi/v1/klines
Parameters:
  - symbol: BTCUSDT
  - interval: 1h, 4h, 1d, etc.
  - startTime: milliseconds
  - endTime: milliseconds
  - limit: max 1500
```

**Funding Rate Endpoint:**
```
GET /fapi/v1/fundingRate
Parameters:
  - symbol: BTCUSDT
  - startTime: milliseconds
  - endTime: milliseconds
  - limit: max 1000
```

### Rate Limits

- **API Limit:** 1200 requests per minute
- **Per Coin:** ~5 requests for 90 days of 1-hour data
- **Safe Throughput:** 240 coins/minute

### Response Format

**Kline Response:**
```json
[
  [
    1577836800000,    // Open time
    "9000.00",        // Open price
    "9500.00",        // High price
    "8900.00",        // Low price
    "9300.00",        // Close price
    "12345.67",       // Volume
    1577923199999,    // Close time
    "114850000.00",   // Quote asset volume
    ...
  ]
]
```

**Funding Rate Response:**
```json
[
  {
    "symbol": "BTCUSDT",
    "fundingRate": "0.00007657",
    "fundingTime": 1609804800000,
    "markPrice": "90456.00"
  }
]
```

---

## Error Handling

The module gracefully handles errors:

```python
# Connection errors
df = binance.fetch_historical_kline('BTCUSDT', days=1)
if df.empty:
    print("Failed to fetch data - check connection")

# Invalid symbol
df = binance.fetch_historical_kline('INVALID', days=1)
# Returns empty DataFrame

# API rate limit (429)
# Module waits and retries automatically

# Invalid timeframe
df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='99h')
# Falls back to '1h' (default)
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Empty DataFrame | No data for symbol | Check symbol is correct |
| Connection timeout | Network issue | Check internet connection |
| HTTP 429 | Rate limited | Wait before retrying |
| Symbol not found | Invalid symbol | Verify symbol on Binance |

---

## Performance Tips

### 1. Batch Processing

```python
# Good: Fetch multiple coins
coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
for coin in coins:
    df = binance.fetch_historical_kline(coin, days=7, resolution='1h')
    process(df)
```

### 2. Reduce Time Ranges

```python
# Good: Fetch 7 days
df = binance.fetch_historical_kline('BTCUSDT', days=7, resolution='1h')

# Better: Fetch 1 day
df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')
```

### 3. Use Appropriate Timeframes

```python
# Good: Use 1-hour for daily analysis
df = binance.fetch_historical_kline('BTCUSDT', days=90, resolution='1h')

# Better: Use 1-day for long-term analysis
df = binance.fetch_historical_kline('BTCUSDT', days=90, resolution='1d')
```

### 4. Cache Data

```python
# Store in InfluxDB for repeated access
# Reduces API calls
# Faster analysis
```

---

## Integration Examples

### With Backfill System

```python
# modules/exchanges/binance.py is used by backfill.py
# backfill.py calls:
#   binance.fetch_historical_kline(symbol, days, resolution)
#   writes to InfluxDB
```

### With Real-time Collector

```python
# Real-time collection example
from modules.exchanges.binance import BinanceFuturesKline

binance = BinanceFuturesKline()

# Fetch current hour + previous hours
df = binance.fetch_historical_kline('BTCUSDT', days=1, resolution='1h')

# Get latest price
latest = df.iloc[-1]
print(f"Current price: ${latest['close']:.2f}")
```

### With Data Analysis

```python
import pandas as pd
from modules.exchanges.binance import BinanceFuturesKline

binance = BinanceFuturesKline()
df = binance.fetch_historical_kline('BTCUSDT', days=30, resolution='1d')

# Calculate returns
df['returns'] = df['close'].pct_change()

# Calculate moving average
df['sma_10'] = df['close'].rolling(10).mean()

# Plot
df[['close', 'sma_10']].plot()
```

---

## Summary

The `BinanceFuturesKline` class provides:

✅ Reliable OHLCV data fetching  
✅ Funding rate support  
✅ Multiple timeframe options  
✅ Automatic batch processing  
✅ Error handling and validation  
✅ Production-ready performance  

**Use for:** Backfill systems, real-time collection, technical analysis, trading bots
