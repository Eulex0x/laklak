# Laklak

> **Cross-Platform Market Data Collector**  
> *Unified data collection from crypto exchanges, stock markets, and commodities - ready for analysis in seconds.*

[![PyPI version](https://img.shields.io/pypi/v/laklak.svg)](https://pypi.org/project/laklak/)
[![Python versions](https://img.shields.io/pypi/pyversions/laklak.svg)](https://pypi.org/project/laklak/)
[![Downloads](https://img.shields.io/pypi/dm/laklak.svg)](https://pypi.org/project/laklak/)
[![License](https://img.shields.io/github/license/Eulex0x/laklak)](https://github.com/Eulex0x/laklak/blob/main/LICENSE)

```bash
pip install laklak
```

---

## 🎯 What is Laklak?

**Laklak** is a production-ready Python application that solves a critical problem for traders, analysts, and data scientists: **fragmented financial data sources**. Instead of writing custom integrations for every exchange or market, Laklak provides a unified solution to collect, validate, and store time-series market data from multiple sources in one central database.

Whether you're tracking Bitcoin on Bybit, monitoring S&P 500 volatility, or analyzing gold prices, Laklak handles the complexity of API integrations, data formatting, and storage - so you can focus on analysis and strategy development.

### The Problem We Solve

- **Data Fragmentation**: Each exchange has different APIs, formats, and rate limits
- **Infrastructure Overhead**: Setting up reliable data pipelines is time-consuming
- **Data Quality**: Missing validation leads to corrupted analysis and failed strategies
- **Scalability**: Manual data collection doesn't scale beyond a few assets
- **Time-Series Storage**: Traditional databases aren't optimized for market data

### The Laklak Solution

✅ **Unified Interface**: One configuration file to rule them all  
✅ **Multi-Source Support**: Crypto, stocks, forex, commodities, volatility indices  
✅ **Production-Ready**: Battle-tested with error handling, logging, and validation  
✅ **Grafana-Ready**: Data flows directly into InfluxDB for instant visualization  
✅ **Extensible Architecture**: Add new exchanges and data sources with minimal code  

---

## 🚀 Multi-Exchange Support

Laklak currently supports:

| Source | Data Type | Assets | Example Symbols |
|--------|-----------|--------|-----------------|
| **Bybit** | OHLCV (1h candles) | Crypto spot & perpetuals | BTCUSDT, ETHUSDT, SOLUSDT |
| **Bybit** | Funding Rates | Perpetual contracts | BTCUSDT_fundingrate_bybit |
| **Deribit** | DVOL (volatility index) | BTC & ETH volatility | BTC_DVOL, ETH_DVOL |
| **Yahoo Finance** | OHLCV (1h candles) | Stocks, indices, forex, commodities | AAPL, ^GSPC, GC=F, EUR=X |

💡 **Coming Soon**: Binance, Kraken, CoinGecko, Alpha Vantage, and more!

---

## ✨ Key Features

- 🔌 **Multi-Exchange Support**: Unified access to Bybit, Deribit, and Yahoo Finance
- 📊 **Multi-Asset Coverage**: Cryptocurrencies, stocks, indices, forex, and commodities
- 💾 **InfluxDB Integration**: Optimized time-series storage with sub-second queries
- 🏷️ **Smart Naming**: Symbols stored as `SYMBOL_EXCHANGE` (e.g., `BTCUSDT_BYBIT`, `AAPL_YFINANCE`)
- ✅ **Data Validation**: Automatic validation prevents corrupted data from entering your database
- ⚡ **Scalable Batching**: Start small (2 assets) and scale to 1000+ for production
- 📝 **Comprehensive Logging**: Track every operation for debugging and monitoring
- 🛡️ **Error Resilience**: One failed API call won't stop your entire collection
- ⏮️ **Historical Backfill**: Populate years of historical data with one command
- ⏰ **Automated Scheduling**: Set it and forget it with cron integration

---

## 🎬 Quick Start - Get Data in 5 Minutes

### Option 1: Use as Python Library (Recommended) 📦

**Install from PyPI:**

```bash
pip install laklak
```

**Use it directly in your code:**

```python
from laklak import collect, backfill, Laklak

# Option A: Simple usage (write to InfluxDB)
collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30)
backfill('ETHUSDT', exchange='bybit', timeframe='4h', period=150)

# Option B: Get data as DataFrame (no InfluxDB needed) ⭐ NEW in v1.0.7
data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30, use_influxdb=False)
btc_df = data['BTCUSDT']  # pandas DataFrame with OHLCV data
print(btc_df.head())
#                      open     high      low    close      volume
# 2024-01-01 00:00:00  42000.0  42100.0  41900.0  42050.0  1234567.0
# 2024-01-01 01:00:00  42050.0  42200.0  42000.0  42150.0  2345678.0

# Multiple symbols return a dictionary
data = collect(['BTCUSDT', 'ETHUSDT'], exchange='bybit', 
               timeframe='5m', period='7d', use_influxdb=False)
btc_df = data['BTCUSDT']
eth_df = data['ETHUSDT']

# Option C: Custom InfluxDB connection
fetcher = Laklak(
    influx_host='192.168.1.100',
    influx_port=8086,
    influx_db='my_market_data',
    influx_username='admin',
    influx_password='secret'
)
fetcher.collect('AAPL', exchange='yfinance', timeframe='1d', period='1y')

# Multiple timeframes supported
collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d')
collect('ETHUSDT', exchange='bybit', timeframe='15m', period='2w')
```

**That's it!** No configuration files needed - just import and use. 🚀

**Prerequisites:**
- Python 3.7+ 🐍
- InfluxDB 1.6+ 💾 (optional - set `use_influxdb=False` if not needed)

---

### Option 2: Use Source Code for Automation

**For scheduled data collection and advanced customization:**

```bash
# Clone the repository
git clone https://github.com/Eulex0x/laklak.git
cd laklak

# Install dependencies
pip3 install -r requirements.txt

# Configure environment (optional for public data)
cp .env.example .env
nano .env  # Add your API keys if needed
```

**Setup InfluxDB (required for both options):**

```bash
# Create database
influx
CREATE DATABASE market_data
CREATE RETENTION POLICY "1_year" ON "market_data" DURATION 52w REPLICATION 1 DEFAULT
exit
```

---

### Configuration for Automation (Option 2)

Edit `assets.txt` to define which assets you want to track:

```plaintext
# Simple format: SYMBOL EXCHANGE [ADDITIONAL_EXCHANGES]

# Crypto from multiple sources
BTCUSDT bybit+deribit          # BTC price + volatility
ETHUSDT bybit+deribit          # ETH price + volatility
SOLUSDT bybit                  # SOL price only

# Traditional markets
AAPL yfinance                  # Apple stock
^GSPC yfinance                 # S&P 500 index
GC=F yfinance                  # Gold futures
BTC-USD yfinance               # Bitcoin from Yahoo Finance
```

Laklak automatically:
- ✅ Fetches from the correct API for each exchange
- ✅ Handles different symbol formats (BTCUSDT vs BTC-USD)
- ✅ Stores with clear naming: `BTCUSDT_BYBIT`, `AAPL_YFINANCE`, `BTC_DVOL`
- ✅ Validates and batch-writes to InfluxDB

**Run the Collector:**

```bash
python3 data_collector.py
```

**Success!** You'll see:

```
2024-12-02 12:00:00 - INFO - Starting market data collection
2024-12-02 12:00:00 - INFO - Loaded 8 assets from assets.txt
2024-12-02 12:00:01 - INFO - [1/8] Processing BTCUSDT from Bybit
2024-12-02 12:00:02 - INFO - ✓ Successfully wrote 24 points for BTCUSDT_BYBIT
2024-12-02 12:00:03 - INFO - [2/8] Processing BTC_DVOL from Deribit
2024-12-02 12:00:04 - INFO - ✓ Successfully wrote 24 points for BTC_DVOL
...
```

### Automate Collection (Optional)

```bash
# Create log directory
mkdir -p logs

# Add to crontab (runs every hour at minute 0)
crontab -e
# Add: 0 * * * * cd /home/user/laklak && /usr/bin/python3 data_collector.py >> logs/collector.log 2>&1
```

---

## 📖 Usage Examples

### Real-Time Data Collection

Collect the latest hourly data for all configured assets:

```bash
python3 data_collector.py
```

**NEW! Automatic Funding Rate Collection** 🎯

When you run `data_collector.py`, it now automatically collects **funding rates** for all Bybit perpetual contracts alongside price data!

**What are Funding Rates?**
- Updated every 8 hours (00:00, 08:00, 16:00 UTC)
- Positive rate = long positions pay short positions
- Negative rate = short positions pay long positions
- Critical for perpetual futures trading strategies

**Storage Format:** `SYMBOL_fundingrate_bybit` (e.g., `BTCUSDT_fundingrate_bybit`)

No extra configuration needed - if you have Bybit assets in `assets.txt`, funding rates are collected automatically!

### Historical Backfill

Populate your database with historical data (up to 1 year):

```bash
python3 backfill.py
```

This fetches historical data for all assets in `assets.txt`.

### Adding New Assets

Simply edit `assets.txt` - no code changes needed:

```plaintext
# Add gold and silver
GC=F yfinance      # Gold futures
SI=F yfinance      # Silver futures

# Add tech stocks
GOOGL yfinance     # Google
MSFT yfinance      # Microsoft

# Add more crypto
AVAXUSDT bybit     # Avalanche
LINKUSDT bybit     # Chainlink
```

Run the collector again - Laklak automatically handles the new assets!

### Flexible Timeframes

Laklak supports **any timeframe** you need:

```python
from laklak import collect, Laklak

# 📊 Minutes: 1m, 3m, 5m, 15m, 30m
collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d')

# ⏰ Hours: 1h, 2h, 4h, 6h, 12h
collect('ETHUSDT', exchange='bybit', timeframe='4h', period='3m')

# 📅 Days/Weeks/Months: 1d, 1w, 1M
collect('AAPL', exchange='yfinance', timeframe='1d', period='1y')

# 🎯 Period formats: days, '7d', '2w', '6m', '1y'
collect('BTCUSDT', exchange='bybit', timeframe='15m', period=14)

# ⭐ NEW: Without InfluxDB - Get data as DataFrame (v1.0.7+)
data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period='7d', use_influxdb=False)
btc_df = data['BTCUSDT']  # pandas DataFrame with columns: open, high, low, close, volume, timestamp
print(f"Got {len(btc_df)} candles")
print(btc_df.describe())  # Statistical summary

# Multiple symbols return a dictionary
data = collect(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], 
               exchange='bybit', timeframe='15m', period=14, use_influxdb=False)
for symbol, df in data.items():
    print(f"{symbol}: {len(df)} rows, price range {df['low'].min()}-{df['high'].max()}")
```

**Smart Limits**: Laklak automatically caps periods to respect Bybit's **1000 candle limit**:
- **1min**: max ~17 hours
- **5min**: max ~3.5 days  
- **15min**: max ~10 days
- **1hour**: max ~42 days (not 1 year!)
- **4hour**: max ~167 days (~5.5 months) - **recommended for backfill**
- **1day**: max ~1000 days (~2.7 years)
- **1week**: longer periods (yfinance supports more)

### Configuration

**Environment Variables (optional):**

```env
# InfluxDB Connection (used if not specified in code)
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_DATABASE=market_data
INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=secret

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/collector.log
```

**Or configure in code:**

```python
from laklak import Laklak

# Custom InfluxDB connection
fetcher = Laklak(
    influx_host='localhost',
    influx_port=8086,
    influx_db='market_data',
    influx_username='admin',
    influx_password='secret'
)

# Or disable InfluxDB completely and get data back
fetcher = Laklak(use_influxdb=False)
data = fetcher.collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30)
# data is now a Dict[str, pd.DataFrame] - use it however you want!
```

### 📊 Working with Returned Data (v1.0.7+)

When `use_influxdb=False`, Laklak returns the data as pandas DataFrames instead of writing to the database:

```python
from laklak import collect, backfill

# Get hourly BTC data for last 30 days
data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30, use_influxdb=False)
btc_df = data['BTCUSDT']

# DataFrame structure:
# - Index: datetime (timezone-aware)
# - Columns: open, high, low, close, volume

# Analyze the data
print(f"Latest close: ${btc_df['close'].iloc[-1]:,.2f}")
print(f"30-day high: ${btc_df['high'].max():,.2f}")
print(f"30-day low: ${btc_df['low'].min():,.2f}")
print(f"Average volume: {btc_df['volume'].mean():,.0f}")

# Calculate returns
btc_df['returns'] = btc_df['close'].pct_change()
print(f"Volatility: {btc_df['returns'].std():.4f}")

# Multiple symbols at once
data = backfill(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'], 
                exchange='bybit', timeframe='4h', period=150, use_influxdb=False)

# Process each symbol
for symbol, df in data.items():
    print(f"\n{symbol}:")
    print(f"  Total candles: {len(df)}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Price change: {((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100):.2f}%")
    
# Save to CSV or use in your own analysis pipeline
btc_df.to_csv('btc_data.csv')
```

**Use Cases for Data Return Mode:**
- 🧪 **Research & Experimentation**: Quick data pulls without database setup
- 🤖 **Custom Processing**: Feed data into your ML pipeline or analysis tools
- 💾 **Alternative Storage**: Save to CSV, Parquet, or your own database
- 📊 **Ad-Hoc Analysis**: Jupyter notebook explorations and one-off analyses
- ⚡ **Lightweight Deployments**: No InfluxDB dependency for simple use cases

---

## 🎯 Who Should Use Laklak?

### 📈 Traders & Quantitative Analysts
Build and backtest strategies with clean, validated historical data from multiple markets.

### 🔬 Data Scientists
Focus on analysis and ML models, not API integration and data cleaning.

### 💼 Financial Analysts
Monitor portfolios across crypto, stocks, and commodities in one unified database.

### 🏢 Research Teams
Centralize market data collection for the entire team with one reliable pipeline.

### 🚀 Startups & Side Projects
Get production-grade infrastructure without building it from scratch.

---

## 🏗️ Architecture

### Data Flow Pipeline

```
┌─────────────────────────────────────────────────────┐
│  Data Sources                                       │
│  • Bybit API      • Deribit API    • Yahoo Finance │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Laklak Core                                         │
│  • data_collector.py  (real-time)                   │
│  • backfill.py        (historical)                  │
│  • Exchange modules   (bybit/deribit/yfinance)      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Data Processing                                    │
│  • Validation       • Normalization                 │
│  • Batching         • Error Handling                │
│  modules/influx_writer.py                           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  InfluxDB Time-Series Database                      │
│  • Measurement: market_data                         │
│  • Retention: 1 year (configurable)                 │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Analysis & Visualization                           │
│  • Grafana Dashboards                               │
│  • Trading Strategies                               │
│  • Custom Analytics                                 │
│  • Machine Learning Models                          │
└─────────────────────────────────────────────────────┘
```

### Database Schema

**Measurement**: `market_data`

| Tag | Description | Example |
|-----|-------------|---------|
| `symbol` | Asset symbol + exchange | `BTCUSDT_BYBIT`, `AAPL_YFINANCE` |
| `exchange` | Data source | `bybit`, `yfinance`, `deribit` |
| `data_type` | Type of data | `kline` (OHLCV), `dvol` (volatility) |

| Field | Description | Type |
|-------|-------------|------|
| `open` | Opening price | Float |
| `high` | Highest price | Float |
| `low` | Lowest price | Float |
| `close` | Closing price | Float |
| `volume` | Trading volume | Float |
| `timestamp` | Event timestamp | Integer (Unix ms) |

---

## 📊 Grafana Integration

Laklak is **Grafana-ready** out of the box! Your data flows directly into InfluxDB and can be visualized instantly.

### Quick Grafana Setup

1. Add InfluxDB as a data source in Grafana
2. Create a new dashboard
3. Use these example queries:

```sql
-- Bitcoin price from Bybit
SELECT mean("close") FROM "market_data" 
WHERE "symbol" = 'BTCUSDT_BYBIT' 
AND $timeFilter 
GROUP BY time($__interval)

-- Bitcoin Funding Rate (NEW!)
SELECT mean("close") FROM "market_data" 
WHERE "symbol" = 'BTCUSDT_fundingrate_bybit' 
AND $timeFilter 
GROUP BY time($__interval)

-- Compare BTC prices across exchanges
SELECT mean("close") FROM "market_data" 
WHERE "symbol" =~ /BTC.*/ 
AND $timeFilter 
GROUP BY time($__interval), "exchange"

-- Track portfolio (multiple assets)
SELECT mean("close") FROM "market_data" 
WHERE "symbol" IN ('BTCUSDT_BYBIT', 'ETHUSDT_BYBIT', 'GC=F_YFINANCE')
AND $timeFilter 
GROUP BY time($__interval), "symbol"

-- Funding Rates for Multiple Assets (NEW!)
SELECT mean("close") FROM "market_data" 
WHERE "symbol" =~ /.*_fundingrate_bybit/ 
AND $timeFilter 
GROUP BY time($__interval), "symbol"
```

**Pro Tip**: Use Grafana template variables to switch between assets dynamically!

---

## 🔍 Monitoring & Debugging

### Log Monitoring

```bash
# Real-time log monitoring
tail -f logs/collector.log

# Search for specific issues
grep ERROR logs/collector.log
grep WARNING logs/collector.log

# Count successful operations
grep "Successfully wrote" logs/collector.log | wc -l
```

### Data Verification

```bash
# Enter InfluxDB CLI
influx

# Query your data
USE market_data

# Total data points collected
SELECT COUNT(*) FROM market_data

# Data points per asset
SELECT COUNT(*) FROM market_data GROUP BY symbol

# Latest data for Bitcoin
SELECT * FROM market_data 
WHERE symbol =~ /BTC/ 
ORDER BY time DESC 
LIMIT 10

# Check data coverage (no gaps)
SELECT COUNT(*) FROM market_data 
WHERE time > now() - 7d 
GROUP BY time(1h), symbol
```

---

## 🚀 Scaling for Production

### From Prototype to Production

Laklak is designed to scale with your needs:

**Phase 1: Testing (2-10 assets)**
```env
INFLUXDB_BATCH_SIZE=2
```

**Phase 2: Small Production (10-100 assets)**
```env
INFLUXDB_BATCH_SIZE=50
```

**Phase 3: Large Production (100-1000+ assets)**
```env
INFLUXDB_BATCH_SIZE=100
```

### Parallel Collection (Advanced)

For 1000+ assets, split the workload:

```bash
# Split assets into chunks
split -l 100 assets.txt assets_chunk_

# Run multiple instances in parallel
python3 data_collector.py assets_chunk_aa &
python3 data_collector.py assets_chunk_ab &
python3 data_collector.py assets_chunk_ac &
```

---

## 🔧 Troubleshooting

### InfluxDB Connection Issues

```bash
# Verify InfluxDB is running
sudo systemctl status influxdb

# Test connection
influx -host localhost -port 8086 -execute "SHOW DATABASES"

# Check InfluxDB logs
sudo journalctl -u influxdb -n 50
```

### No Data Being Written

1. **Check logs**: `tail -f logs/collector.log`
2. **Verify database**: `influx -execute "SHOW DATABASES"`
3. **Validate assets.txt**: Ensure symbols are correctly formatted
4. **Test API access**: Try fetching data manually

### Data Quality Issues

```bash
# Check for null values
influx -execute 'SELECT * FROM market_data WHERE close = 0 LIMIT 10'

# Verify timestamps are recent
influx -execute 'SELECT * FROM market_data ORDER BY time DESC LIMIT 5'
```

### Rate Limiting

If you hit API rate limits:
- Reduce batch size temporarily
- Add delays between requests in code
- Use API keys for higher limits (Bybit, etc.)

---

## 🛠️ Integration Examples

### Using Data in Python Trading Strategies

```python
from influxdb import InfluxDBClient
import pandas as pd

# Connect to InfluxDB
client = InfluxDBClient(host='localhost', port=8086, database='market_data')

# Query Bitcoin data
query = """
    SELECT * FROM market_data 
    WHERE symbol = 'BTCUSDT_BYBIT' 
    AND time > now() - 7d
"""
result = client.query(query)

# Convert to pandas DataFrame
df = pd.DataFrame(result.get_points())
print(df.head())

# Calculate indicators
df['sma_20'] = df['close'].rolling(window=20).mean()
df['volatility'] = df['close'].pct_change().rolling(window=20).std()
```

### Using Data in Node.js Applications

```javascript
const Influx = require('influx');

const influx = new Influx.InfluxDB({
  host: 'localhost',
  database: 'market_data',
  schema: [{
    measurement: 'market_data',
    fields: {
      open: Influx.FieldType.FLOAT,
      high: Influx.FieldType.FLOAT,
      low: Influx.FieldType.FLOAT,
      close: Influx.FieldType.FLOAT,
      volume: Influx.FieldType.FLOAT
    },
    tags: ['symbol', 'exchange']
  }]
});

// Query data
influx.query(`
  SELECT * FROM market_data 
  WHERE symbol = 'ETHUSDT_BYBIT' 
  ORDER BY time DESC 
  LIMIT 100
`).then(result => {
  console.log(result);
});
```

---

## 📂 Project Structure

```
laklak/
├── data_collector.py          # Real-time data collection (OHLCV + funding rates)
├── backfill.py                # Historical data backfill
├── config.py                  # Centralized configuration
├── assets.txt                 # Asset configuration file
├── requirements.txt           # Python dependencies
├── LICENSE                    # MIT License
├── README.md                  # This file
│

└── modules/                   # Core modules
    ├── __init__.py
    ├── influx_writer.py       # InfluxDB writer with validation
    └── exchanges/             # Exchange-specific modules
        ├── __init__.py
        ├── bybit.py           # Bybit OHLCV + funding rates
        ├── deribit.py         # Deribit DVOL integration
        └── yfinance.py        # Yahoo Finance integration
```

---

## 🌟 Vision & Roadmap

### The Big Picture

Laklak is evolving into the **ultimate all-in-one financial data library** - think of it as the "requests" or "pandas" of market data. Our goal is to make accessing any financial data as simple as:

```python
from laklak import collect

# Collect any asset from any source
collect("BTCUSDT", source="bybit")
collect("AAPL", source="yfinance")
collect("BTC_DVOL", source="deribit")
```

### Roadmap

**Q1 2025**
- [ ] 🔄 Real-time WebSocket support (live data streaming)
- [x] 📦 PyPI package release (`pip install laklak`)
- [ ] 🌐 Binance & Kraken integration
- [ ] 🔍 Advanced anomaly detection

**Q2 2025**
- [ ] ⏱️ Multi-timeframe support (5m, 15m, 4h, 1d candles)
- [ ] 📊 Built-in technical indicators
- [ ] 🤖 Automated data quality reports
- [ ] 🐳 Docker deployment

**Q3 2025**
- [ ] 🌍 CoinGecko & CoinMarketCap integration
- [ ] 📈 Alpha Vantage & Polygon.io support
- [ ] 🧮 On-chain data (Etherscan, etc.)
- [ ] 📚 Comprehensive API documentation

**Long-term Vision**
- [ ] 🚀 Cloud-native deployment (AWS, GCP, Azure)
- [ ] 🔌 Plugin architecture for custom data sources
- [ ] 🤝 Integration with popular trading frameworks
- [ ] 🌐 Web UI for monitoring and configuration

---

## 🤝 Contributing

We welcome contributions from the community! Whether it's:

- 🐛 Bug reports and fixes
- ✨ New features and enhancements
- 📝 Documentation improvements
- 🔌 New exchange integrations
- 💡 Ideas and suggestions

**How to Contribute:**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Sublicense

---

## 💬 Support & Community

### Get Help

- 📖 **Documentation**: Check the [`Info/`](Info/) directory
- 🐛 **Issues**: [GitHub Issues](https://github.com/Eulex0x/laklak/issues)
- 💡 **Discussions**: [GitHub Discussions](https://github.com/Eulex0x/laklak/discussions)

### Stay Updated

- ⭐ Star this repository to follow updates
- 👀 Watch for new releases
- 🔔 Enable notifications for important updates

---

## 🙏 Acknowledgments

Built with ❤️ by [Eulex0x](https://github.com/Eulex0x)

Special thanks to:
- InfluxData for InfluxDB
- The open-source community
- All contributors and users

---

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/Eulex0x/laklak?style=social)
![GitHub forks](https://img.shields.io/github/forks/Eulex0x/laklak?style=social)
![GitHub issues](https://img.shields.io/github/issues/Eulex0x/laklak)
![GitHub license](https://img.shields.io/github/license/Eulex0x/laklak)

---

<div align="center">

**Made with ❤️ for the trading and data science community**

[⬆ Back to top](#laklak)

</div>
