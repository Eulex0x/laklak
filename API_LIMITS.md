# API Limits & Best Practices

Understanding exchange API limitations and how Laklak handles them.

## 🚨 Critical: 1000 Candle Limit

**All major exchanges (Bybit, Binance, etc.) limit API responses to 1000 candles per request.**

This is why you can't fetch "1 year of 1-hour data" in one request:
- 1 year = 365 days = 8,760 hours = **8,760 candles** ❌
- API limit = **1,000 candles** ✅

## 📊 Actual Limits per Timeframe

Based on 1000 candle limit:

| Timeframe | Minutes | Max Period | Days | Candles |
|-----------|---------|------------|------|---------|
| **1m** | 1 | 16.7 hours | 0.7 | 1000 |
| **3m** | 3 | 50 hours | 2.1 | 1000 |
| **5m** | 5 | 83.3 hours | 3.5 | 1000 |
| **15m** | 15 | 250 hours | 10.4 | 1000 |
| **30m** | 30 | 500 hours | 20.8 | 1000 |
| **1h** | 60 | 1000 hours | **41.7** ⚠️ | 1000 |
| **2h** | 120 | 2000 hours | 83.3 | 1000 |
| **4h** | 240 | 4000 hours | **166.7** ✅ | 1000 |
| **6h** | 360 | 6000 hours | 250 | 1000 |
| **12h** | 720 | 12000 hours | 500 | 1000 |
| **1d** | 1440 | 1000 days | **2.7 years** | 1000 |
| **1w** | 10080 | 7000 days | **19 years** | 1000 |

### Key Takeaways

✅ **Best for long periods**: 4h, 1d, 1w timeframes
⚠️ **Limited**: 1h gives you only ~42 days max
❌ **Very limited**: 5m gives you only ~3.5 days max

## 🎯 Recommended Defaults

### Laklak Defaults (Updated)

```python
# collect() - for recent data
# Default: 1h timeframe, 30 days (~720 candles)
collect('BTCUSDT', exchange='bybit')

# backfill() - for historical data
# Default: 4h timeframe, 150 days (~900 candles)
backfill('BTCUSDT', exchange='bybit')
```

**Why these defaults?**
- ✅ Under 1000 candle limit
- ✅ Good balance of detail and history
- ✅ Works reliably across all exchanges

## ⚡ Smart Auto-Limiting

Laklak automatically caps your requested period:

```python
# You request 1 year of hourly data
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=365)

# ⚠️ Laklak warns and caps to 42 days:
# "WARNING: Requested 365 days exceeds maximum 42 days for 1h timeframe. 
#  Capping to 42 days."

# Result: You get 42 days (1000 candles) instead of error
```

## 📝 Safe Usage Examples

### ✅ Within Limits

```python
from laklak import collect

# 5min: 3 days (864 candles)
collect('BTCUSDT', exchange='bybit', timeframe='5m', period=3)

# 15min: 10 days (960 candles)
collect('BTCUSDT', exchange='bybit', timeframe='15m', period=10)

# 1hour: 40 days (960 candles)
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=40)

# 4hour: 150 days (900 candles) ✅ BEST for backfill!
collect('BTCUSDT', exchange='bybit', timeframe='4h', period=150)

# 1day: 2 years (730 candles)
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='2y')

# 1day: 2.5 years (912 candles)
collect('BTCUSDT', exchange='bybit', timeframe='1d', period=912)
```

### ❌ Will be Auto-Capped

```python
# Requested → Actual
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=365)  # → 42 days
collect('BTCUSDT', exchange='bybit', timeframe='5m', period=30)   # → 3.5 days
collect('BTCUSDT', exchange='bybit', timeframe='15m', period=60)  # → 10 days
```

## 🔄 Getting More Historical Data

### Option 1: Use Larger Timeframes

Instead of:
```python
# ❌ 1 hour, 1 year (8760 candles - IMPOSSIBLE)
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=365)
```

Do this:
```python
# ✅ 4 hour, 1 year (2190 candles - but capped to 167 days/1000 candles)
collect('BTCUSDT', exchange='bybit', timeframe='4h', period=365)

# ✅ Daily, 2 years (730 candles - PERFECT!)
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='2y')
```

### Option 2: Multiple Requests (Manual Loop)

For fine-grained historical data, you need to loop:

```python
from laklak import collect
from datetime import datetime, timedelta

def collect_year_of_hourly_data(symbol, exchange='bybit'):
    """
    Collect 1 year of hourly data by making multiple requests.
    Each request gets ~40 days (960 candles).
    """
    # Need ~9 requests to cover 365 days with 40-day chunks
    for i in range(9):
        days_back_start = i * 40
        days_back_end = (i + 1) * 40
        
        print(f"Fetching days {days_back_start}-{days_back_end}...")
        # Note: This would require custom start_date parameter
        # Current API doesn't support this yet - feature for v2.0!
        
    print("✅ Collected 1 year of hourly data in 9 requests")

# Current workaround: Use daily timeframe instead
collect('BTCUSDT', exchange='bybit', timeframe='1d', period=365)
```

### Option 3: Use Daily Timeframe for Backtesting

For strategy backtesting, daily candles are often sufficient:

```python
# ✅ 5 years of daily data (1825 candles - but capped to 1000 days)
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='5y')

# Result: You get ~2.7 years (1000 days) of data
```

## 🎓 Real-World Strategies

### Scalping (1-5 minute candles)
```python
# Short lookback, frequent updates
collect('BTCUSDT', exchange='bybit', timeframe='1m', period=0.5)  # 12 hours
collect('BTCUSDT', exchange='bybit', timeframe='5m', period=3)    # 3 days
```

### Day Trading (5-15 minute candles)
```python
# 1-2 weeks of data
collect('BTCUSDT', exchange='bybit', timeframe='5m', period=3)    # 3 days
collect('BTCUSDT', exchange='bybit', timeframe='15m', period=10)  # 10 days
```

### Swing Trading (1-4 hour candles)
```python
# 1-3 months of data
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=40)   # 40 days
collect('BTCUSDT', exchange='bybit', timeframe='4h', period=150)  # 5 months
```

### Position Trading (4h - daily candles)
```python
# 6 months to 2 years
collect('BTCUSDT', exchange='bybit', timeframe='4h', period=167)  # 5.5 months
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='2y') # 2 years
```

### Long-term Analysis (daily - weekly)
```python
# Multiple years
collect('BTCUSDT', exchange='bybit', timeframe='1d', period=912)  # 2.5 years
collect('BTC-USD', exchange='yfinance', timeframe='1w', period='10y') # 10 years
```

## 📊 Exchange-Specific Notes

### Bybit
- ✅ 1000 candle limit per request
- ✅ Reliable for crypto pairs (BTCUSDT, ETHUSDT, etc.)
- ⚠️ Historical data varies by pair (new pairs = less history)

### Deribit (DVOL)
- ✅ 1000 candle limit
- ✅ BTC and ETH volatility index only
- ⚠️ Less historical data than price data

### Yahoo Finance
- ✅ More generous limits
- ✅ Long historical data (stocks: decades)
- ⚠️ Slower API response times
- ✅ Best for daily/weekly long-term data

## 🛠️ Future Features (v2.0)

Planned features to handle large historical requests:

```python
# Automatic chunking for large periods
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=365, auto_chunk=True)
# → Laklak makes 9 requests automatically

# Specify date ranges
collect('BTCUSDT', exchange='bybit', 
        timeframe='1h',
        start_date='2024-01-01',
        end_date='2024-12-31')

# Progress callback
def progress(current, total):
    print(f"Progress: {current}/{total} chunks")

collect('BTCUSDT', exchange='bybit', timeframe='1h', 
        period=365, auto_chunk=True, callback=progress)
```

## 💡 Best Practices

1. **Match timeframe to your needs**
   - Don't collect 1-minute data if you're swing trading
   - Don't collect daily data if you're scalping

2. **Use 4h timeframe for long backtests**
   - Best balance: 167 days (~5.5 months) in one request
   - Good detail for most strategies

3. **Use daily timeframe for multi-year analysis**
   - Get 2.7 years (1000 days) in one request
   - Perfect for position trading backtests

4. **Start with defaults**
   - `collect()`: 1h, 30 days - good for recent data
   - `backfill()`: 4h, 150 days - good for historical data

5. **Monitor warnings**
   - Laklak warns when capping periods
   - Adjust your timeframe if hitting limits frequently

## 📈 Summary Table

| Use Case | Timeframe | Period | Candles | Why |
|----------|-----------|--------|---------|-----|
| **Scalping** | 1m-5m | 12h-3d | <1000 | Real-time decisions |
| **Day Trading** | 5m-15m | 3d-10d | <1000 | Intraday patterns |
| **Swing Trading** | 1h-4h | 40d-150d | <1000 | Multi-day trends |
| **Position Trading** | 4h-1d | 150d-2y | <1000 | Long-term trends |
| **Backtesting** | 4h | 150d | ~900 | ✅ Best balance |
| **Long-term Analysis** | 1d | 2y | ~730 | ✅ Multiple years |

---

**Remember**: API limits are there to prevent abuse. Laklak respects them automatically! 🎯
