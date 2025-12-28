# Hyperliquid Funding Rate Format Reference

## Data Format

Hyperliquid funding rates are stored in **decimal format** (not scientific notation display).

### Examples
- `0.0001` = 0.01% funding rate per 8 hours
- `1.00635e-05` = 0.001006% funding rate per 8 hours
- `-6.412e-07` = -0.00006412% funding rate per 8 hours

## Format Conversions

### Using the Helper Functions

```python
from modules.exchanges.hyperliquid import HyperliquidKline

hyperliquid = HyperliquidKline()
rate = 0.0001  # 0.01% per 8 hours

# Different format outputs
print(hyperliquid.format_funding_rate(rate, 'decimal'))        # 0.0001
print(hyperliquid.format_funding_rate(rate, 'percentage'))     # 0.0100000000%
print(hyperliquid.format_funding_rate(rate, 'basis_points'))   # 1.0000 bp
print(hyperliquid.format_funding_rate(rate, 'fixed'))          # 0.00010000

# Annualized rate
annual = hyperliquid.convert_rate_to_annual(rate, 8)
print(f"{annual:.2f}%")  # 10.95%
```

### Manual Conversions

```python
rate = 0.0001  # Decimal format from API/database

# To percentage
percentage = rate * 100
# Output: 0.01%

# To basis points (1 bp = 0.0001 = 0.01%)
basis_points = rate * 10000
# Output: 1 bp

# To annualized (8-hour periods)
periods_per_year = 365 * 24 / 8  # 1095 periods
annualized = rate * 100 * periods_per_year
# Output: 10.95%
```

## Display Formats

### Format 1: Decimal (Default)
```
Rate: 0.0001
Meaning: 0.01% per 8 hours
Usage: Raw value from API/database
```

### Format 2: Percentage
```
Rate × 100 = 0.01%
Display: "0.01% per 8 hours"
Usage: Human readable percentage
```

### Format 3: Basis Points
```
Rate × 10000 = 1 bp
Display: "1 bp per 8 hours"
Usage: Financial reporting
```

### Format 4: Fixed Decimal (8 places)
```
Format: f"{rate:.8f}"
Output: "0.00010000"
Usage: Consistent precision in logs/reports
```

### Format 5: Annualized Rate
```
Annual = rate × 100 × (365×24/period_hours)
For 8-hour periods: 0.0001 × 100 × 1095 = 10.95%
Display: "10.95% annually"
Usage: Comparing returns
```

## Real Data Examples from InfluxDB

```
Raw Value (Decimal)  | Percentage     | Basis Points | Annualized
─────────────────────┼────────────────┼──────────────┼───────────
0.0001               | 0.01%          | 1 bp         | 10.95%
0.00005              | 0.005%         | 0.5 bp       | 5.48%
-0.00003             | -0.003%        | -0.3 bp      | -3.29%
1.00635e-05          | 0.001006%      | 0.1006 bp    | 1.10%
-6.412e-07           | -0.00006412%   | -0.0064 bp   | -0.07%
```

## Processing Further

### In SQL Queries

```sql
-- Get rates as percentage
SELECT close * 100 as percentage FROM market_data 
WHERE exchange='Hyperliquid' AND data_type='funding_rate'

-- Get rates as basis points
SELECT close * 10000 as basis_points FROM market_data 
WHERE exchange='Hyperliquid' AND data_type='funding_rate'

-- Annualized rate (for 8-hour periods: 1095 per year)
SELECT close * 100 * 1095 as annual_rate FROM market_data 
WHERE exchange='Hyperliquid' AND data_type='funding_rate'
```

### In Python (InfluxDB Query Results)

```python
import requests

response = requests.get('http://192.168.4.3:8086/query', params={
    'db': 'market_data',
    'q': "SELECT close FROM market_data WHERE exchange='Hyperliquid'"
})

data = response.json()
for value in data['results'][0]['series'][0]['values']:
    timestamp, close = value
    
    # Different formats
    decimal = close                          # 0.0001
    percentage = close * 100                 # 0.01
    basis_points = close * 10000             # 1
    annual = close * 100 * 1095              # 10.95
    
    print(f"Decimal: {decimal}, Percentage: {percentage}%, BP: {basis_points}, Annual: {annual}%")
```

## Key Points

✅ **Storage**: Always stored as decimal in InfluxDB  
✅ **Range**: Typically -0.001 to 0.001 (extremely small percentages)  
✅ **Precision**: 8+ decimal places preserved  
✅ **Annualization**: Use 1095 periods/year for 8-hour funding periods  
✅ **Easy Conversion**: Multiply by 100 for percentage, 10000 for basis points  

## Visual Representation

```
0.0001 Decimal Format
  │
  ├─ × 100 ──→ 0.01% (Percentage)
  │
  ├─ × 10000 ──→ 1 bp (Basis Points)
  │
  └─ × 100 × 1095 ──→ 10.95% (Annualized)
```

## Common Use Cases

### Track Daily Funding Income
```python
rate = 0.0001  # 0.01% per 8 hours
daily_income = rate * 3  # 3 funding periods per day
annual_income = rate * 100 * 365 * 3  # Annualized
```

### Compare Funding Rates Across Exchanges
```python
# All in decimal format for easy comparison
hl_rate = 0.0001      # Hyperliquid
bybit_rate = 0.00008  # Bybit
bitunix_rate = 0.00012 # Bitunix

# Percentage comparison
print(f"HL: {hl_rate*100}% vs Bybit: {bybit_rate*100}% vs Bitunix: {bitunix_rate*100}%")
```

### Alert on High Funding Rates
```python
# Alert if funding rate exceeds 0.01% (1 basis point) per period
threshold = 0.0001

if abs(rate) > threshold:
    print(f"⚠️  High funding rate detected: {rate*10000:.2f} bp")
```

## Notes

- Hyperliquid uses **8-hour funding periods** for all perpetuals
- Funding rates can be positive (longs pay shorts) or negative (shorts pay longs)
- Very small rates (like 1e-07) are valid and represent near-zero funding
- Scientific notation (1e-05) is just display format; actual value is 0.00001
