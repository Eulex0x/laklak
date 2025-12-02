# Laklak v1.0.7 Release Notes

## 🎉 Major Feature: Data Return Mode

### What's New?

Starting with v1.0.7, Laklak can now **return collected data as pandas DataFrames** instead of only writing to InfluxDB. This makes the library much more flexible and useful for research, experimentation, and custom data pipelines.

### The Problem

Previous versions (1.0.0-1.0.6) only wrote data to InfluxDB. If you set `use_influxdb=False`, the data would be collected but you had no way to access it - it would just be logged and discarded.

### The Solution

Now when `use_influxdb=False`, the `collect()` and `backfill()` methods return the collected data:

```python
from laklak import collect

# Before v1.0.7: Data was lost if InfluxDB disabled
# After v1.0.7: Get data as DataFrames!

data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30, use_influxdb=False)
btc_df = data['BTCUSDT']  # pandas DataFrame with OHLCV data

print(btc_df.head())
#                      open     high      low    close      volume
# 2024-01-01 00:00:00  42000.0  42100.0  41900.0  42050.0  1234567.0
# 2024-01-01 01:00:00  42050.0  42200.0  42000.0  42150.0  2345678.0
```

## 📋 Technical Changes

### Return Types

**Before:**
```python
def collect(...) -> bool:  # Always returned True/False
```

**After:**
```python
def collect(...) -> Union[bool, Dict[str, pd.DataFrame]]:
    # Returns bool when use_influxdb=True (backward compatible)
    # Returns Dict[str, pd.DataFrame] when use_influxdb=False (new!)
```

### Implementation Details

1. **Added imports** in `laklak/core.py`:
   - `from typing import Dict`
   - `import pandas as pd`

2. **Modified `collect()` method**:
   - Added `collected_data` dictionary to store DataFrames when InfluxDB disabled
   - Stores raw DataFrame (`df_raw`) from each exchange before conversion
   - Returns `collected_data` dict when `use_influxdb=False`
   - Returns `bool` when `use_influxdb=True` (backward compatible)

3. **Updated `backfill()` method**:
   - Changed return type to match `collect()`
   - Inherits same behavior since it calls `collect()`

4. **Updated convenience functions**:
   - `collect()` standalone function: Updated return type and documentation
   - `backfill()` standalone function: Updated return type and documentation

## 🚀 Use Cases

### 1. Research & Experimentation
```python
# Quick data pulls without database setup
data = collect('BTCUSDT', exchange='bybit', timeframe='5m', period='7d', use_influxdb=False)
df = data['BTCUSDT']
df['returns'] = df['close'].pct_change()
print(f"Volatility: {df['returns'].std():.4f}")
```

### 2. Machine Learning Pipelines
```python
# Fetch data and feed directly into ML pipeline
from laklak import collect
import tensorflow as tf

data = collect(['BTCUSDT', 'ETHUSDT'], exchange='bybit', 
               timeframe='1h', period=90, use_influxdb=False)

# Prepare training data
features = prepare_features(data)
model.fit(features, labels)
```

### 3. Custom Storage
```python
# Save to CSV, Parquet, or your own database
data = collect('AAPL', exchange='yfinance', timeframe='1d', period='1y', use_influxdb=False)
aapl_df = data['AAPL']

# Save to different formats
aapl_df.to_csv('aapl_2023.csv')
aapl_df.to_parquet('aapl_2023.parquet')
aapl_df.to_sql('aapl_prices', engine, if_exists='replace')
```

### 4. Jupyter Notebook Analysis
```python
# Perfect for exploratory data analysis
import matplotlib.pyplot as plt

data = collect('BTCUSDT', exchange='bybit', timeframe='4h', period=150, use_influxdb=False)
df = data['BTCUSDT']

# Quick visualization
df['close'].plot(title='BTC Price (4H)', figsize=(12, 6))
plt.show()
```

## 📦 DataFrame Structure

The returned DataFrames have the following structure:

- **Index**: DatetimeIndex (timezone-aware timestamps)
- **Columns**:
  - `open`: Opening price
  - `high`: Highest price in the period
  - `low`: Lowest price in the period
  - `close`: Closing price
  - `volume`: Trading volume

Example:
```python
data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period=24, use_influxdb=False)
df = data['BTCUSDT']

print(df.info())
# DatetimeIndex: 24 entries
# Data columns (total 5 columns):
#  #   Column   Non-Null Count  Dtype  
# ---  ------   --------------  -----  
#  0   open     24 non-null     float64
#  1   high     24 non-null     float64
#  2   low      24 non-null     float64
#  3   close    24 non-null     float64
#  4   volume   24 non-null     float64
```

## 🔄 Backward Compatibility

**100% backward compatible!** 

All existing code continues to work exactly as before. If you don't specify `use_influxdb=False`, the behavior is identical to previous versions:

```python
# This works exactly the same as v1.0.6 and earlier
collect('BTCUSDT', exchange='bybit')  # Writes to InfluxDB, returns bool
```

## 📥 Upgrade Instructions

### From PyPI
```bash
pip install --upgrade laklak
```

### Verify Version
```python
import laklak
print(laklak.__version__)  # Should print: 1.0.7
```

## 📝 Documentation Updates

- Updated README.md with DataFrame usage examples
- Added new section "Working with Returned Data"
- Updated all docstrings with return type information
- Added examples for both InfluxDB and DataFrame modes

## 🔗 Resources

- **PyPI Package**: https://pypi.org/project/laklak/1.0.7/
- **GitHub Repository**: https://github.com/Eulex0x/laklak
- **Full Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 👏 Credits

This feature was implemented based on user feedback requesting a way to access collected data when InfluxDB is disabled.

---

**Install now:**
```bash
pip install laklak==1.0.7
```

Happy data collecting! 🚀
