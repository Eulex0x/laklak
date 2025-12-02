# Market Data Collector

A production-ready Python application for collecting and storing 1-hour OHLCV market data from multiple exchanges and data sources in InfluxDB. This system serves as a centralized data repository that can be used by multiple trading strategies and analytical tools.

> **🚀 NEW: Multi-Exchange Support!** Now supports Bybit (crypto), Deribit (volatility), and Yahoo Finance (stocks, indices, forex, commodities). See [`MULTI_EXCHANGE_GUIDE.md`](MULTI_EXCHANGE_GUIDE.md) for details.

## Features

- **Multi-Exchange Support**: Collect data from Bybit, Deribit, and Yahoo Finance
- **Multi-Asset Support**: Cryptocurrencies, stocks, indices, forex, and commodities
- **InfluxDB Integration**: Efficient time-series data storage and retrieval
- **Exchange-Specific Naming**: Symbols stored as `SYMBOL_EXCHANGE` (e.g., `BTCUSDT_BYBIT`, `AAPL_YFINANCE`)
- **Data Validation**: Automatic validation of data before writing to database
- **Configurable Batching**: Start with small batches and scale to 1000+ for production
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Error Resilience**: Graceful error handling that continues processing on failures
- **Historical Backfill**: One-time script to populate database with historical data
- **Automated Scheduling**: Easy cron integration for hourly data collection

## Quick Start

### 1. Prerequisites

- Python 3.7+
- InfluxDB 1.6+
- Bybit API access (free tier available)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Eulex0x/market_data.git
cd market_data

# Install dependencies
pip3 install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. Configure InfluxDB

```bash
# Create database
influx
CREATE DATABASE market_data
CREATE RETENTION POLICY "1_year" ON "market_data" DURATION 52w REPLICATION 1 DEFAULT
exit
```

### 4. Add Coins to Track

Edit `coins.txt` and add the symbols you want to track:

```
BTCUSDT
ETHUSDT
SOLUSDT
BNBUSDT
XRPUSDT
# Add more coins, one per line
```

### 5. Test the Collector

```bash
python3 data_collector.py
```

You should see output like:

```
2024-01-15 12:00:00 - data_collector - INFO - Starting market data collection
2024-01-15 12:00:00 - data_collector - INFO - Loaded 5 coins from coins.txt
2024-01-15 12:00:01 - data_collector - INFO - [1/5] Processing BTCUSDT
2024-01-15 12:00:02 - data_collector - INFO - Successfully processed 2 points for BTCUSDT
...
```

### 6. Set Up Automatic Collection

```bash
# Create log directory
mkdir -p /var/log/market_data

# Create run script
cat > run_collector.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/market_data
/usr/bin/python3 data_collector.py >> /var/log/market_data/collector.log 2>&1
EOF

chmod +x run_collector.sh

# Add to crontab (runs every hour)
crontab -e
# Add: 0 * * * * /home/ubuntu/market_data/run_collector.sh
```

## Usage

### Daily Data Collection

The data collector runs every hour via cron and fetches the latest 1-hour candles for all coins:

```bash
python3 data_collector.py
```

### Historical Data Backfill

To populate the database with historical data (one-time operation):

```bash
python3 backfill.py
```

This will fetch up to 365 days of historical data for all coins in `coins.txt`.

### Configuration

Edit `.env` to customize:

```env
# InfluxDB settings
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_DATABASE=market_data
INFLUXDB_BATCH_SIZE=2  # Start small, increase for production

# Data collection
RESOLUTION_KLINE=60  # 1 hour
DAYS=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/market_data/collector.log
```

## Architecture

### Data Flow

```
Bybit API
    ↓
data_collector.py (or backfill.py)
    ↓
InfluxDB Writer (modules/influx_writer.py)
    ↓
InfluxDB (market_data database)
    ↓
Grafana / Trading Strategies
```

### InfluxDB Schema

All data is stored in a single measurement called `market_data`:

| Tag      | Description                    |
| :------- | :----------------------------- |
| `symbol` | Trading pair (e.g., BTCUSDT)   |
| `exchange` | Exchange name (e.g., Bybit)  |
| `data_type` | Data type (e.g., kline)     |

| Field    | Description                    |
| :------- | :----------------------------- |
| `open`   | Opening price                  |
| `high`   | Highest price                  |
| `low`    | Lowest price                   |
| `close`  | Closing price                  |
| `volume` | Trading volume                 |

### InfluxDB Writer Module

The `modules/influx_writer.py` module handles:

- **Data Validation**: Checks for null values, correct types, valid ranges
- **Batching**: Groups data points for efficient writes
- **Error Handling**: Skips invalid data, logs warnings
- **Connection Management**: Handles InfluxDB connection lifecycle

## Monitoring

### Check Logs

```bash
# View recent logs
tail -f /var/log/market_data/collector.log

# Search for errors
grep ERROR /var/log/market_data/collector.log
```

### Query Data in InfluxDB

```bash
influx

# Inside the influx shell:
USE market_data

# Count total points
SELECT COUNT(*) FROM market_data

# Count points per symbol
SELECT COUNT(*) FROM market_data GROUP BY symbol

# View latest data for a symbol
SELECT * FROM market_data WHERE symbol = 'BTCUSDT' ORDER BY time DESC LIMIT 5
```

## Scaling

### Increase Batch Size

For better performance in production, increase the batch size:

```env
INFLUXDB_BATCH_SIZE=100  # Increased from 2
```

Recommended sizes:
- **Testing**: 2-10
- **Small production**: 50-100
- **Large production**: 500-1000

### Parallel Collection

For 1000+ coins, run multiple collector instances:

```bash
# Split coins.txt
split -l 100 coins.txt coins_

# Run in parallel
python3 data_collector.py coins_aa &
python3 data_collector.py coins_ab &
```

## Troubleshooting

### Connection Issues

```bash
# Check InfluxDB status
sudo systemctl status influxdb

# Test connection
influx -host localhost -port 8086 -execute "SHOW DATABASES"
```

### No Data Written

1. Check logs: `tail -f /var/log/market_data/collector.log`
2. Verify database exists: `influx -execute "SHOW DATABASES"`
3. Verify coins.txt has valid symbols
4. Check Bybit API accessibility

### Performance Issues

1. Increase batch size in `.env`
2. Check InfluxDB disk space: `df -h`
3. Monitor InfluxDB CPU: `top`
4. Consider running multiple collector instances

## Integration with Other Tools

### Using Data in Grafana

1. Add InfluxDB as a data source in Grafana
2. Create dashboards that query the `market_data` measurement
3. Use template variables to switch between coins

### Using Data in Trading Strategies

Query the InfluxDB database from your trading strategy:

```python
from influxdb import InfluxDBClient

client = InfluxDBClient(host='localhost', port=8086, database='market_data')
result = client.query('SELECT * FROM market_data WHERE symbol = "BTCUSDT" LIMIT 10')
```

## Project Structure

```
market_data/
├── data_collector.py      # Main data collection script
├── backfill.py            # Historical data backfill script
├── config.py              # Configuration management
├── coins.txt              # List of coins to track
├── .env.example           # Example environment configuration
├── requirements.txt       # Python dependencies
└── modules/
    ├── influx_writer.py   # InfluxDB writer module
    ├── bybit_klin.py      # Bybit API wrapper for OHLCV data
    ├── deribit_dvol.py    # Deribit API wrapper for volatility data
    ├── data.py            # Data loading utilities
    ├── iv_plot.py         # Visualization utilities
    └── iv_shock.py        # IV shock detection logic
```

## Dependencies

- `requests` - HTTP library for API calls
- `python-dotenv` - Environment variable management
- `pandas` - Data manipulation and analysis
- `influxdb-client` - InfluxDB Python client

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the project maintainer.

## Roadmap

- [ ] Support for additional exchanges (Binance, Kraken, etc.)
- [ ] Real-time data streaming via WebSocket
- [ ] Advanced data validation and anomaly detection
- [ ] Automated data quality reports
- [ ] Multi-timeframe data collection (5m, 15m, 4h, 1d, etc.)
- [ ] Integration with popular trading frameworks

## Changelog

### v1.0.0 (2024-01-15)
- Initial release
- Support for Bybit OHLCV data
- InfluxDB 1.6 integration
- Configurable batching and logging
- Historical data backfill
- Comprehensive documentation
