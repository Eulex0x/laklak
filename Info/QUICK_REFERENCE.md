# Quick Reference - Multi-Exchange Market Data Collector

## 📁 New Structure
```
modules/
  ├── influx_writer.py   # InfluxDB writer
  └── exchanges/
      ├── bybit.py       # Crypto futures (BTCUSDT, ETHUSDT, etc.)
      ├── deribit.py     # Volatility index (BTC, ETH DVOL)
      └── yfinance.py    # Stocks, crypto, indices (AAPL, BTC-USD, ^GSPC, etc.)

assets.txt               # Your asset configuration file
```

## 📝 Asset Configuration (`assets.txt`)

### Format
```
SYMBOL EXCHANGE [+EXCHANGE2+EXCHANGE3...]
```

### Examples
```
# Crypto from multiple sources
BTCUSDT bybit+deribit
ETHUSDT bybit+deribit

# Crypto from single source
SOLUSDT bybit
DOGEUSDT bybit

# Stocks via Yahoo Finance
AAPL yfinance
GOOGL yfinance
MSFT yfinance
TSLA yfinance

# Crypto via Yahoo Finance
BTC-USD yfinance
ETH-USD yfinance

# Indices
^GSPC yfinance    # S&P 500
^DJI yfinance     # Dow Jones
^VIX yfinance     # Volatility Index

# Forex
EURUSD=X yfinance
GBPUSD=X yfinance

# Commodities
GC=F yfinance     # Gold Futures
CL=F yfinance     # Crude Oil Futures
```

## 🏷️ Database Symbol Naming

**Price Data:** `SYMBOL_EXCHANGE`  
**Volatility Data:** `BASECURRENCY_DVOL`

| Asset | Source | Type | Stored As |
|-------|--------|------|-----------|
| BTCUSDT | bybit | Price | `BTCUSDT_BYBIT` |
| BTC | deribit | Volatility | `BTC_DVOL` |
| ETH | deribit | Volatility | `ETH_DVOL` |
| BTC-USD | yfinance | Price | `BTC-USD_YFINANCE` |
| AAPL | yfinance | Price | `AAPL_YFINANCE` |
| ^GSPC | yfinance | Price | `^GSPC_YFINANCE` |

## 🔍 InfluxDB Query Examples

```sql
-- BTC price from Bybit
SELECT * FROM market_data WHERE symbol = 'BTCUSDT_BYBIT'

-- BTC implied volatility
SELECT * FROM market_data WHERE symbol = 'BTC_DVOL'

-- All price data for BTC across exchanges
SELECT * FROM market_data WHERE symbol =~ /^BTC.*_(BYBIT|YFINANCE)$/

-- All assets from Yahoo Finance
SELECT * FROM market_data WHERE exchange = 'YFinance'

-- Compare BTC price across exchanges
SELECT mean("close") FROM market_data 
WHERE symbol =~ /^BTC.*_(BYBIT|YFINANCE)$/
AND time > now() - 24h
GROUP BY time(1h), symbol

-- BTC price with volatility
SELECT mean("close") FROM market_data 
WHERE (symbol = 'BTCUSDT_BYBIT' OR symbol = 'BTC_DVOL')
AND time > now() - 24h
GROUP BY time(1h), symbol

-- All kline data (price)
SELECT * FROM market_data WHERE data_type = 'kline'

-- All DVOL data (volatility)
SELECT * FROM market_data WHERE data_type = 'dvol'
```

## 🚀 Usage

```bash
# Run data collector
python data_collector.py

# Run backfill (historical data)
python backfill.py
```

## 📊 Grafana Query Template

```sql
SELECT mean("close") 
FROM "market_data" 
WHERE symbol =~ /^${SYMBOL}_/ 
AND $timeFilter 
GROUP BY time($__interval), symbol, exchange
```

## 🔧 Common Yahoo Finance Symbols

| Type | Examples |
|------|----------|
| **Crypto** | BTC-USD, ETH-USD, DOGE-USD, ADA-USD |
| **Stocks** | AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN |
| **Indices** | ^GSPC (S&P 500), ^DJI (Dow), ^IXIC (NASDAQ), ^VIX |
| **Forex** | EURUSD=X, GBPUSD=X, JPYUSD=X |
| **Commodities** | GC=F (Gold), CL=F (Oil), SI=F (Silver) |

## ⚙️ Supported Intervals

| Exchange | Format | Examples |
|----------|--------|----------|
| Bybit | String/Number | "1", "5", "15", "60", "D", "W" |
| Deribit | String/Number | "1", "60", "3600", "1D" |
| YFinance | String | "1m", "5m", "1h", "1d", "1wk", "1mo" |

**Auto-conversion:** System converts Bybit "60" to Yahoo Finance "1h" automatically

## 📋 Tags in InfluxDB

Each data point has these tags:
- `symbol` - Full symbol with exchange (e.g., `BTCUSDT_BYBIT`)
- `exchange` - Exchange name (e.g., `Bybit`, `YFinance`, `Deribit`)
- `data_type` - Type of data (e.g., `kline`, `dvol`)

## 🎯 Quick Start Checklist

1. ✅ Edit `assets.txt` with your desired assets
2. ✅ Run `python data_collector.py`
3. ✅ Check logs for successful data collection
4. ✅ Query InfluxDB with new symbol format
5. ✅ Update Grafana dashboards

## 💡 Pro Tips

1. **Mix asset types**: Combine crypto, stocks, and indices in one dashboard
2. **Compare exchanges**: Use regex to select all exchanges for one asset
3. **Filter efficiently**: Use tags (exchange, data_type) for fast queries
4. **Monitor volatility**: Combine DVOL (Deribit) with price (Bybit/YFinance)
5. **Cross-market analysis**: Compare crypto with traditional markets (^VIX, ^GSPC)

## 🔗 More Information

- `MULTI_EXCHANGE_GUIDE.md` - Comprehensive guide
- `MIGRATION_SUMMARY.md` - What changed and why
- `SETUP_GUIDE.md` - Original setup instructions
