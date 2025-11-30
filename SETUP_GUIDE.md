# Setup Guide for Market Data Collector

This guide provides detailed step-by-step instructions for setting up the market data collector on your system.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [InfluxDB Installation](#influxdb-installation)
3. [Python Environment Setup](#python-environment-setup)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Automation](#automation)
7. [Monitoring](#monitoring)

---

## System Requirements

- **OS**: Linux (Ubuntu 18.04+, Debian 9+) or macOS
- **Python**: 3.7 or higher
- **InfluxDB**: 1.6 or higher
- **Disk Space**: At least 10GB for initial data collection
- **RAM**: 2GB minimum, 4GB recommended
- **Network**: Stable internet connection for API calls

---

## InfluxDB Installation

### Ubuntu/Debian

```bash
# Add InfluxDB repository
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/os-release
echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

# Update and install
sudo apt-get update
sudo apt-get install influxdb

# Start the service
sudo systemctl start influxdb
sudo systemctl enable influxdb  # Enable on boot

# Verify installation
influx -version
```

### macOS (using Homebrew)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install InfluxDB
brew install influxdb

# Start the service
brew services start influxdb

# Verify installation
influx -version
```

### Create Database and Retention Policy

```bash
# Connect to InfluxDB
influx

# Inside the influx shell, run these commands:
CREATE DATABASE market_data
CREATE RETENTION POLICY "1_year" ON "market_data" DURATION 52w REPLICATION 1 DEFAULT
SHOW DATABASES
SHOW RETENTION POLICIES ON "market_data"

# Exit
exit
```

---

## Python Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Eulex0x/market_data.git
cd market_data
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip3 install -r requirements.txt
```

Verify installation:

```bash
python3 -c "import influxdb; import pandas; print('All dependencies installed successfully')"
```

---

## Configuration

### 1. Create Environment File

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

### 2. Configure InfluxDB Connection

Edit `.env` and set:

```env
INFLUXDB_HOST=localhost
INFLUXDB_PORT=8086
INFLUXDB_DATABASE=market_data
INFLUXDB_USERNAME=
INFLUXDB_PASSWORD=
INFLUXDB_BATCH_SIZE=2
```

### 3. Configure Data Collection

```env
RESOLUTION_KLINE=60  # 1 hour
DAYS=10
```

### 4. Configure Logging

```env
LOG_LEVEL=INFO
LOG_FILE=/var/log/market_data/collector.log
```

### 5. Create Log Directory

```bash
sudo mkdir -p /var/log/market_data
sudo chown $USER:$USER /var/log/market_data
```

### 6. Add Coins to Track

Edit `coins.txt` and add the symbols you want to collect:

```bash
cat > coins.txt << 'EOF'
BTCUSDT
ETHUSDT
SOLUSDT
BNBUSDT
XRPUSDT
ADAUSDT
DOGEUSDT
LTCUSDT
LINKUSDT
UNIUSDT
EOF
```

You can add up to 1000+ coins, one per line.

---

## Testing

### 1. Test InfluxDB Connection

```bash
# Verify InfluxDB is running
sudo systemctl status influxdb

# Test connection
influx -host localhost -port 8086 -execute "SHOW DATABASES"
```

### 2. Test Configuration

```bash
# Verify configuration is loaded correctly
python3 -c "from config import print_config; print_config()"
```

### 3. Test Data Collector

```bash
# Run the collector manually
python3 data_collector.py
```

Expected output:

```
2024-01-15 12:00:00 - data_collector - INFO - ================================================================================
2024-01-15 12:00:00 - data_collector - INFO - Starting market data collection
2024-01-15 12:00:00 - data_collector - INFO - ================================================================================
2024-01-15 12:00:00 - data_collector - INFO - Loaded 10 coins from coins.txt
2024-01-15 12:00:01 - data_collector - INFO - [1/10] Processing BTCUSDT
2024-01-15 12:00:02 - data_collector - INFO - Successfully processed 2 points for BTCUSDT
...
```

### 4. Verify Data in InfluxDB

```bash
# Connect to InfluxDB
influx

# Inside the influx shell:
USE market_data
SELECT COUNT(*) FROM market_data
SELECT * FROM market_data LIMIT 5
```

---

## Automation

### 1. Create Run Script

```bash
# Create the run script
cat > run_collector.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/market_data
/usr/bin/python3 data_collector.py >> /var/log/market_data/collector.log 2>&1
EOF

# Make it executable
chmod +x run_collector.sh
```

### 2. Set Up Cron Job

```bash
# Edit crontab
crontab -e

# Add this line to run the collector every hour at the start of the hour:
0 * * * * /home/ubuntu/market_data/run_collector.sh

# Save and exit (in nano: Ctrl+X, then Y, then Enter)
```

### 3. Verify Cron Job

```bash
# List your cron jobs
crontab -l

# Check cron logs (on Linux)
grep CRON /var/log/syslog | tail -20
```

---

## Monitoring

### 1. Check Logs

```bash
# View recent logs
tail -f /var/log/market_data/collector.log

# View last 100 lines
tail -100 /var/log/market_data/collector.log

# Search for errors
grep ERROR /var/log/market_data/collector.log

# Count successful collections
grep "Successfully processed" /var/log/market_data/collector.log | wc -l
```

### 2. Monitor InfluxDB

```bash
# Check InfluxDB status
sudo systemctl status influxdb

# View InfluxDB logs
sudo journalctl -u influxdb -n 50 -f

# Check disk usage
df -h /var/lib/influxdb
```

### 3. Query Data Statistics

```bash
influx

# Inside the influx shell:
USE market_data

# Count total points
SELECT COUNT(*) FROM market_data

# Count points per symbol
SELECT COUNT(*) FROM market_data GROUP BY symbol

# Count points per hour
SELECT COUNT(*) FROM market_data GROUP BY time(1h) LIMIT 10

# Find latest data
SELECT * FROM market_data ORDER BY time DESC LIMIT 5

# Find data for specific symbol
SELECT * FROM market_data WHERE symbol = 'BTCUSDT' ORDER BY time DESC LIMIT 10
```

### 4. Set Up Alerts (Optional)

Create a simple monitoring script:

```bash
cat > monitor.sh << 'EOF'
#!/bin/bash

# Check if InfluxDB is running
if ! sudo systemctl is-active --quiet influxdb; then
    echo "ERROR: InfluxDB is not running!"
    sudo systemctl start influxdb
fi

# Check if data was collected in the last 2 hours
LAST_UPDATE=$(influx -execute "SELECT * FROM market_data ORDER BY time DESC LIMIT 1" | tail -1 | awk '{print $1}')
echo "Last data update: $LAST_UPDATE"

# Check disk usage
DISK_USAGE=$(df /var/lib/influxdb | tail -1 | awk '{print $5}')
echo "InfluxDB disk usage: $DISK_USAGE"

if [ "${DISK_USAGE%\%}" -gt 80 ]; then
    echo "WARNING: Disk usage is above 80%"
fi
EOF

chmod +x monitor.sh
```

---

## Troubleshooting

### InfluxDB Connection Issues

**Problem**: "Failed to connect to InfluxDB"

**Solution**:
```bash
# Check if InfluxDB is running
sudo systemctl status influxdb

# Start InfluxDB if not running
sudo systemctl start influxdb

# Check if port 8086 is listening
netstat -tuln | grep 8086

# Test connection
influx -host localhost -port 8086 -execute "SHOW DATABASES"
```

### No Data Being Written

**Problem**: Data collector runs but no data in InfluxDB

**Solution**:
```bash
# Check logs for errors
tail -50 /var/log/market_data/collector.log

# Verify coins.txt is not empty
cat coins.txt

# Test with a single coin
python3 -c "
from modules.bybit_klin import BybitKline
bybit = BybitKline()
df = bybit.fetch_historical_kline('BTCUSDT', days=1, resolution=60)
print(f'Fetched {len(df)} rows')
print(df.head())
"

# Verify InfluxDB database exists
influx -execute "SHOW DATABASES"
```

### Cron Job Not Running

**Problem**: Cron job is scheduled but not executing

**Solution**:
```bash
# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify the script is executable
ls -la run_collector.sh

# Test the script manually
./run_collector.sh

# Check if the script path is correct in crontab
crontab -l

# Verify Python path
which python3
```

### High Disk Usage

**Problem**: InfluxDB is consuming too much disk space

**Solution**:
```bash
# Check InfluxDB disk usage
du -sh /var/lib/influxdb

# Check retention policy
influx -execute "SHOW RETENTION POLICIES ON market_data"

# Create a more aggressive retention policy
influx -execute "ALTER RETENTION POLICY \"1_year\" ON \"market_data\" DURATION 26w"

# Set up downsampling for old data
# (See InfluxDB documentation for continuous queries)
```

---

## Next Steps

1. **Verify data collection**: Run `data_collector.py` and check logs
2. **Set up cron job**: Schedule hourly collection
3. **Monitor performance**: Check logs and InfluxDB metrics regularly
4. **Scale up**: Increase batch size and add more coins as needed
5. **Integrate with Grafana**: Create dashboards for visualization
6. **Integrate with trading strategies**: Query data from your trading algorithms

---

## Support

For issues or questions:

1. Check the logs: `tail -f /var/log/market_data/collector.log`
2. Verify InfluxDB is running: `sudo systemctl status influxdb`
3. Test the connection: `influx -execute "SHOW DATABASES"`
4. Open an issue on GitHub with relevant logs and error messages
