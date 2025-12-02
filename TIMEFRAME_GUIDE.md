# Laklak Timeframe & Period Guide

Complete reference for all supported timeframes and periods in Laklak.

## 📊 Supported Timeframes

Laklak supports a wide range of timeframes to match your analysis needs:

### Minutes
| Timeframe | Alternative | Resolution | Max Period |
|-----------|-------------|------------|------------|
| `1m` | `1min` | 1 minute | 7 days |
| `3m` | `3min` | 3 minutes | 14 days |
| `5m` | `5min` | 5 minutes | 30 days |
| `15m` | `15min` | 15 minutes | 60 days |
| `30m` | `30min` | 30 minutes | 90 days |

### Hours
| Timeframe | Alternative | Resolution | Max Period |
|-----------|-------------|------------|------------|
| `1h` | `1hour` | 1 hour | 365 days (1 year) |
| `2h` | `2hour` | 2 hours | 730 days (2 years) |
| `4h` | `4hour` | 4 hours | 730 days (2 years) |
| `6h` | `6hour` | 6 hours | 1095 days (3 years) |
| `12h` | `12hour` | 12 hours | 1095 days (3 years) |

### Days/Weeks/Months
| Timeframe | Alternative | Resolution | Max Period |
|-----------|-------------|------------|------------|
| `1d` | `1day` | 1 day | 1825 days (5 years) |
| `1w` | `1week` | 1 week | 3650 days (10 years) |
| `1M` | `1month` | 1 month | 3650 days (10 years) |

## ⏰ Period Formats

You can specify periods in multiple formats:

### Integer (Days)
```python
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30)  # 30 days
collect('ETHUSDT', exchange='bybit', timeframe='4h', period=90)  # 90 days
collect('AAPL', exchange='yfinance', timeframe='1d', period=365) # 365 days
```

### String Format
| Format | Meaning | Example Value |
|--------|---------|---------------|
| `'Xd'` | X days | `'7d'`, `'30d'`, `'90d'` |
| `'Xw'` | X weeks | `'1w'`, `'2w'`, `'4w'` |
| `'Xm'` | X months (30 days each) | `'1m'`, `'3m'`, `'6m'` |
| `'Xy'` | X years (365 days each) | `'1y'`, `'2y'`, `'5y'` |

```python
collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d')   # 7 days
collect('ETHUSDT', exchange='bybit', timeframe='1h', period='2w')   # 2 weeks
collect('SOLUSDT', exchange='bybit', timeframe='4h', period='3m')   # 3 months
collect('AAPL', exchange='yfinance', timeframe='1d', period='1y')   # 1 year
```

## 🎯 Common Use Cases

### Scalping & Day Trading (Short-term)
```python
# 1-minute candles, last 24 hours
collect('BTCUSDT', exchange='bybit', timeframe='1m', period=1)

# 5-minute candles, last week
collect('ETHUSDT', exchange='bybit', timeframe='5m', period='7d')

# 15-minute candles, last 2 weeks
collect('SOLUSDT', exchange='bybit', timeframe='15m', period=14)
```

### Swing Trading (Medium-term)
```python
# 1-hour candles, last month
collect('BTCUSDT', exchange='bybit', timeframe='1h', period='30d')

# 4-hour candles, last 3 months
collect('ETHUSDT', exchange='bybit', timeframe='4h', period='3m')

# Daily candles, last 6 months
collect('AAPL', exchange='yfinance', timeframe='1d', period='6m')
```

### Position Trading & Analysis (Long-term)
```python
# Daily candles, last year
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='1y')

# Daily candles, 5 years for backtesting
collect(['AAPL', 'GOOGL', 'MSFT'], exchange='yfinance', timeframe='1d', period='5y')

# Weekly candles, 10 years for macro analysis
collect('BTC-USD', exchange='yfinance', timeframe='1w', period='10y')
```

### Multiple Assets & Timeframes
```python
from laklak import collect

# Scalping portfolio (5min candles)
scalping_assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
collect(scalping_assets, exchange='bybit', timeframe='5m', period='7d')

# Swing trading portfolio (4h candles)
swing_assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
collect(swing_assets, exchange='bybit', timeframe='4h', period='3m')

# Long-term stock portfolio (daily candles)
stock_portfolio = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
collect(stock_portfolio, exchange='yfinance', timeframe='1d', period='2y')
```

## 🔄 Backfill with Timeframes

The `backfill()` function uses the same timeframe syntax but with longer default periods:

```python
from laklak import backfill

# Default: 1 hour candles, 1 year
backfill('BTCUSDT', exchange='bybit')

# 5-minute candles, last month (max for 5m)
backfill('ETHUSDT', exchange='bybit', timeframe='5m', period='30d')

# Daily candles, 5 years
backfill('BTCUSDT', exchange='bybit', timeframe='1d', period='5y')

# Multiple stocks, daily candles, 2 years
backfill(['AAPL', 'GOOGL'], exchange='yfinance', timeframe='1d', period='2y')
```

## ⚠️ Automatic Period Limiting

Laklak **automatically caps** your requested period to respect:
1. **API Rate Limits** - Prevents excessive requests
2. **Data Availability** - Most exchanges don't keep ultra-fine data forever
3. **Performance** - Keeps queries fast and manageable

If you request too much data, you'll see a warning:

```
WARNING: Requested 60 days exceeds maximum 30 days for 5min timeframe. Capping to 30 days.
```

### Recommended Limits

| Timeframe | Recommended Max | Why |
|-----------|----------------|-----|
| 1m - 5m | 7-30 days | High granularity = limited history |
| 15m - 1h | 30-365 days | Good balance of detail and history |
| 4h - 1d | 1-5 years | Perfect for backtesting strategies |
| 1w - 1M | 5-10 years | Long-term macro analysis |

## 💡 Pro Tips

### 1. Match Timeframe to Strategy
```python
# Scalping: Use 1m-5m for real-time decisions
collect('BTCUSDT', exchange='bybit', timeframe='1m', period='1d')

# Day trading: Use 5m-15m for intraday patterns
collect('BTCUSDT', exchange='bybit', timeframe='15m', period='7d')

# Swing trading: Use 1h-4h for multi-day patterns
collect('BTCUSDT', exchange='bybit', timeframe='4h', period='90d')

# Position trading: Use 1d for long-term trends
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='1y')
```

### 2. Multi-Timeframe Analysis
```python
# Analyze same asset on different timeframes
symbol = 'BTCUSDT'

collect(symbol, exchange='bybit', timeframe='15m', period='7d')   # Short-term
collect(symbol, exchange='bybit', timeframe='1h', period='30d')   # Medium-term
collect(symbol, exchange='bybit', timeframe='1d', period='365d')  # Long-term
```

### 3. Optimize Storage
```python
# For backtesting: Use daily candles (less storage)
collect('BTCUSDT', exchange='bybit', timeframe='1d', period='5y')

# For live trading: Use appropriate resolution
collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d')
```

### 4. Combine with Multiple Exchanges
```python
# Get Bitcoin from multiple sources
collect('BTCUSDT', exchange='bybit', timeframe='1h', period='30d')
collect('BTC-USD', exchange='yfinance', timeframe='1h', period='30d')

# Compare in Grafana using symbol tags
```

## 🚀 Advanced Examples

### Strategy Backtesting Setup
```python
from laklak import collect

# 1. Collect 5 years of daily data for backtesting
assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
collect(assets, exchange='bybit', timeframe='1d', period='5y')

# 2. Collect 3 months of 4h data for strategy optimization
collect(assets, exchange='bybit', timeframe='4h', period='3m')

# 3. Collect 1 week of 15m data for recent validation
collect(assets, exchange='bybit', timeframe='15m', period='7d')
```

### Live Trading Setup
```python
from laklak import collect
import schedule
import time

def collect_live_data():
    """Collect latest candles for live trading"""
    assets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    # Collect last 24h of 5-minute data
    collect(assets, exchange='bybit', timeframe='5m', period=1)
    print(f"✅ Collected data at {datetime.now()}")

# Run every 5 minutes
schedule.every(5).minutes.do(collect_live_data)

while True:
    schedule.run_pending()
    time.sleep(1)
```

### Portfolio Monitoring
```python
from laklak import collect

# Crypto portfolio
crypto = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
collect(crypto, exchange='bybit', timeframe='1h', period='30d')

# Stock portfolio
stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
collect(stocks, exchange='yfinance', timeframe='1d', period='1y')

# Commodities
commodities = ['GC=F', 'SI=F', 'CL=F']  # Gold, Silver, Oil
collect(commodities, exchange='yfinance', timeframe='1d', period='1y')
```

## 📚 Quick Reference

```python
from laklak import collect, backfill

# Timeframes: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M
# Periods: integer (days) or string ('7d', '2w', '3m', '1y')

# Simple (defaults: 1h timeframe, 30d period)
collect('BTCUSDT', exchange='bybit')

# Custom timeframe and period
collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d')

# Backfill (defaults: 1h timeframe, 365d period)
backfill('BTCUSDT', exchange='bybit')

# Custom backfill
backfill('BTCUSDT', exchange='bybit', timeframe='1d', period='5y')
```

---

**Need help?** Open an issue on [GitHub](https://github.com/Eulex0x/laklak/issues)
