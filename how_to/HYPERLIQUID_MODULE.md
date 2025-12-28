# Hyperliquid Exchange Module

## Overview

The Hyperliquid module (`modules/exchanges/hyperliquid.py`) provides integration with the Hyperliquid exchange API for fetching current funding rates. This module follows the same architecture as other exchange modules in the project (Bybit, Bitunix, Deribit).

## Features

- **Funding Rate Fetching**: Get current and historical funding rates for perpetual contracts
- **Fixed 8-Hour Funding Period**: Hyperliquid uses a standardized 8-hour funding rate settlement period
- **POST-based API**: Uses Hyperliquid's REST API with POST requests to `https://api.hyperliquid.xyz/info`
- **Error Handling**: Robust error handling for network timeouts and API failures
- **DataFrame Output**: Returns data in standardized pandas DataFrame format for compatibility with InfluxDB writer

## Class: HyperliquidKline

### Methods

#### `fetch_funding_rate_period(coin: str) -> dict`

Returns metadata about the funding rate settlement period.

**Parameters:**
- `coin` (str): Coin symbol (e.g., "BTC", "ETH", "SOL")

**Returns:**
```python
{
    "coin": "BTC",
    "fundingInterval": 8,              # Hours
    "fundingIntervalMinutes": 480,
    "timestamp": 1766931587572,        # Milliseconds since epoch
    "method": "constant",              # Fixed for Hyperliquid
    "note": "Hyperliquid uses fixed 8-hour funding rate period"
}
```

**Note:** Hyperliquid always uses an 8-hour funding period for all perpetuals, so this method returns a constant value.

#### `fetch_funding_rate(coin: str, days: int = 1) -> pd.DataFrame`

Fetches the most recent funding rate for a coin.

**Parameters:**
- `coin` (str): Coin symbol (e.g., "BTC", "ETH", "SOL")
- `days` (int): Number of days of history to fetch for context (default: 1)

**Returns:**
```
pd.DataFrame with columns:
- time: Timestamp (UTC)
- open: Funding rate (as decimal)
- high: Funding rate (same as close)
- low: Funding rate (same as close)
- close: Funding rate (as decimal)
- volume: 0.0 (not applicable for funding rates)
```

**Example:**
```python
df = hyperliquid.fetch_funding_rate("BTC", days=1)
# Output:
#                               time    open    high     low          close  volume
# 0 2025-12-28 14:00:00.095000+00:00  1.006e-07 1.006e-07 1.006e-07 1.006e-07     0.0
```

#### `get_latest_funding_rate(coin: str) -> dict`

Convenience method to get the most recent funding rate as a dictionary.

**Parameters:**
- `coin` (str): Coin symbol (e.g., "BTC", "ETH")

**Returns:**
```python
{
    'coin': 'BTC',
    'fundingRate': 1.00635e-07,
    'time': Timestamp('2025-12-28 14:00:00.095000', tz='UTC'),
    'success': True
}
```

#### `fetch_historical_kline(currency: str, days: int, resolution: int, ...) -> pd.DataFrame`

Placeholder method for OHLC candlestick data.

**Note:** Hyperliquid does not provide historical candlestick data through their API. Use other exchanges (Bybit, Bitunix, Deribit) for OHLC data.

## API Details

### Hyperliquid Funding History Endpoint

**URL:** `https://api.hyperliquid.xyz/info`

**Method:** POST

**Request Payload:**
```json
{
    "type": "fundingHistory",
    "coin": "BTC",
    "startTime": 1681923833000
}
```

**Response Format:**
```json
[
    {
        "time": 1681923833000,
        "fundingRate": "0.000100635"
    },
    ...
]
```

**Supported Coins:**
- BTC, ETH, SOL, AVAX, ARB, OP, DOGE, LINK, ATOM, UNI, LTC, MATIC, BCH, PEPE, SUI, XRP, MKR, STX, BLUR, SEI, and many others
- Check Hyperliquid's documentation for the complete list of supported perpetuals

## Integration with Data Collector

### Configuration in assets.csv

To enable Hyperliquid funding rate collection for a symbol, add `hyperliquid` to the `funding_rate_exchanges` column:

```csv
BTCUSDT,bybit+deribit+bitunix,bitunix+bybit+hyperliquid
ETHUSDT,bybit+deribit+bitunix,bitunix+bybit+hyperliquid
SOLUSDT,bybit+bitunix,bitunix+bybit+hyperliquid
```

### Data Collection Flow

1. **Data Collector** reads `assets.csv` and identifies symbols with `hyperliquid` in `funding_rate_exchanges`
2. **Coin Extraction**: Extracts base coin from symbol (e.g., "BTC" from "BTCUSDT")
3. **Funding Period**: Retrieves the 8-hour funding period (constant)
4. **Funding Rate**: Calls `fetch_funding_rate(coin)` to get current rate
5. **Database Write**: Writes data to InfluxDB with:
   - `exchange` tag: "Hyperliquid"
   - `symbol` tag: Original symbol (e.g., "BTCUSDT")
   - `data_type` tag: "funding_rate"
   - `period` tag: "8"
   - `close` field: Funding rate value

### Example Data Collector Usage

```python
from data_collector import DataCollector, setup_logging

logger = setup_logging('logs/data_collector.log', 'INFO')
collector = DataCollector(logger, batch_size=2)
collector.collect()  # Runs all configured exchanges including Hyperliquid
```

## Data Normalization

Hyperliquid funding rates are returned as percentages (e.g., "0.000100635" = 0.0001% funding rate).

The module automatically converts these to decimals:
- API returns: `"0.000100635"` (percentage string)
- Stored as: `1.00635e-07` (decimal float)

This normalization ensures consistency with other exchanges like Bybit and Bitunix.

## Error Handling

The module handles various failure scenarios gracefully:

### Timeout Error
```python
>>> df = hyperliquid.fetch_funding_rate("INVALID_COIN", days=1)
# Returns empty DataFrame
# Logs: "Timeout fetching funding rate for INVALID_COIN from Hyperliquid"
```

### Request Error
```python
# Returns empty DataFrame if network connection fails
# Logs: "Failed to fetch funding rate for BTC from Hyperliquid: ..."
```

### Invalid Response
```python
# Returns empty DataFrame if response format is unexpected
# Logs: "Error processing funding rate for BTC from Hyperliquid: ..."
```

## Performance Considerations

- **API Rate Limits**: Hyperliquid has generous rate limits; typical usage won't hit them
- **Network Latency**: API calls typically complete in 100-500ms
- **Timeout**: Set to 10 seconds per request
- **Batch Writes**: Data collector batches writes to InfluxDB for efficiency

## Testing

### Quick Test of the Module

```python
from modules.exchanges.hyperliquid import HyperliquidKline

hyperliquid = HyperliquidKline()

# Test 1: Get period (always 8 hours)
period = hyperliquid.fetch_funding_rate_period("BTC")
print(period)

# Test 2: Get current funding rate
df = hyperliquid.fetch_funding_rate("BTC")
print(df)

# Test 3: Get multiple coins
for coin in ["BTC", "ETH", "SOL"]:
    latest = hyperliquid.get_latest_funding_rate(coin)
    print(f"{coin}: {latest['fundingRate']}")
```

### Test with Data Collector

```bash
cd /home/eulex/projects/laklak

# Run with debug logging to see Hyperliquid data collection
timeout 300 ./test_env/bin/python data_collector.py debug=true 2>&1 | grep -i hyperliquid

# Run complete collection (all symbols)
./test_env/bin/python data_collector.py
```

## InfluxDB Query Examples

### Get Latest Hyperliquid Funding Rate for BTC

```sql
SELECT last(close) FROM market_data 
WHERE exchange='Hyperliquid' 
  AND data_type='funding_rate' 
  AND symbol='BTCUSDT'
```

### Compare Funding Rates Across Exchanges

```sql
SELECT last(close) FROM market_data 
WHERE exchange IN ('Hyperliquid', 'Bybit', 'Bitunix')
  AND data_type='funding_rate'
  AND symbol='ETHUSDT'
GROUP BY exchange
```

### Recent Funding Rates for All Coins

```sql
SELECT LAST(close) FROM market_data 
WHERE exchange='Hyperliquid' 
  AND data_type='funding_rate'
GROUP BY symbol
LIMIT 20
```

## Troubleshooting

### No Data Being Collected

1. **Check assets.csv**: Ensure `hyperliquid` is in the `funding_rate_exchanges` column
2. **Check logs**: Run with `debug=true` to see detailed logging
3. **Test API manually**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"type":"fundingHistory","coin":"BTC","startTime":1681923833000}' \
     https://api.hyperliquid.xyz/info
   ```

### Timeouts
- Check network connectivity to `https://api.hyperliquid.xyz`
- Hyperliquid API endpoint may be experiencing issues
- Check if coin is supported on Hyperliquid perpetuals

### Empty DataFrame
- Ensure coin is spelled correctly (e.g., "BTC" not "BTCUSDT")
- Check if coin is supported on Hyperliquid (some smaller coins may not be)

## Architecture Notes

This module follows the consistent architecture pattern used across all exchange modules:

1. **Static Methods**: All methods are static for simplicity and testability
2. **DataFrame Output**: All market data methods return pandas DataFrames with consistent column structure
3. **Dictionary Output**: Metadata (period info, latest rates) returned as dictionaries
4. **Error Handling**: Graceful failures with informative logging
5. **Configuration**: Timezone-aware UTC timestamps for all data

## Future Enhancements

Potential improvements for the module:

1. **Historical Funding Rates**: Hyperliquid API supports historical rates - could add trending/analysis
2. **Batch Requests**: Support fetching rates for multiple coins in fewer requests
3. **Caching**: Add optional caching for period data since it's constant
4. **Performance Metrics**: Track API response times and success rates
5. **Advanced Filtering**: Allow filtering by funding rate direction (positive/negative)

## References

- [Hyperliquid API Documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)
- Hyperliquid Exchange: https://hyperliquid.xyz
- Project Architecture: See other exchange modules (bybit.py, bitunix.py) for patterns
