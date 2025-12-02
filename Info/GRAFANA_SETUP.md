# Grafana Candlestick Chart Setup Guide

## Step 1: Add InfluxDB Data Source

1. Open Grafana (usually at `http://localhost:3000`)
2. Go to **Configuration** (⚙️) → **Data Sources**
3. Click **Add data source**
4. Select **InfluxDB**
5. Configure:
   - **Name**: `Market Data`
   - **Query Language**: `InfluxQL` (for InfluxDB 1.x)
   - **URL**: `http://localhost:8086`
   - **Database**: `market_data`
   - **User**: (leave empty if no auth)
   - **Password**: (leave empty if no auth)
6. Click **Save & Test**

## Step 2: Create a New Dashboard

1. Click **+** → **Create Dashboard**
2. Click **Add visualization**
3. Select your **Market Data** data source

## Step 3: Configure Candlestick Chart

### Option A: Using Candlestick Panel (Recommended)

1. **Panel Type**: Select **Candlestick** (if available)
   - If not available, install the plugin: Go to Configuration → Plugins → search "Candlestick"
   - Or use this plugin: https://grafana.com/grafana/plugins/fifemon-graphql-datasource/

2. **Query Configuration**:

```sql
SELECT 
  mean("open") AS "open",
  mean("high") AS "high", 
  mean("low") AS "low",
  mean("close") AS "close",
  mean("volume") AS "volume"
FROM "market_data" 
WHERE 
  "symbol" = 'BTCUSDT' AND 
  "exchange" = 'Bybit' AND 
  $timeFilter
GROUP BY time($__interval)
```

3. **Query Settings**:
   - Format: `Time series`
   - Alias: Leave empty or use `$tag_symbol`

### Option B: Using Time Series Panel (Alternative)

If candlestick plugin is not available, you can use a Time series panel:

1. **Panel Type**: Select **Time Series**

2. **Add 4 Queries** (A, B, C, D):

**Query A (Close Price)**:
```sql
SELECT mean("close") AS "close"
FROM "market_data"
WHERE "symbol" = 'BTCUSDT' AND $timeFilter
GROUP BY time($__interval) fill(previous)
```
- Alias: `Close`
- Display as: Line

**Query B (High Price)**:
```sql
SELECT mean("high") AS "high"
FROM "market_data"
WHERE "symbol" = 'BTCUSDT' AND $timeFilter
GROUP BY time($__interval) fill(previous)
```
- Alias: `High`
- Display as: Line (dotted)

**Query C (Low Price)**:
```sql
SELECT mean("low") AS "low"
FROM "market_data"
WHERE "symbol" = 'BTCUSDT' AND $timeFilter
GROUP BY time($__interval) fill(previous)
```
- Alias: `Low`
- Display as: Line (dotted)

**Query D (Volume - Optional)**:
```sql
SELECT mean("volume") AS "volume"
FROM "market_data"
WHERE "symbol" = 'BTCUSDT' AND $timeFilter
GROUP BY time($__interval) fill(previous)
```
- Alias: `Volume`
- Display as: Bars (use right Y-axis)

3. **Panel Settings**:
   - Title: `BTCUSDT Price Chart`
   - Legend: Show legend (bottom)

### Option C: Install Candlestick Plugin (Best Option)

**Install ACE.SVG Candlestick Panel**:

```bash
# Method 1: Using grafana-cli
grafana-cli plugins install aceiot-svg-panel

# Method 2: Using Docker (if running Grafana in Docker)
docker exec -it <grafana-container> grafana-cli plugins install aceiot-svg-panel

# Restart Grafana after installation
sudo systemctl restart grafana-server
```

**Or install AJAX Panel for better candlesticks**:
```bash
grafana-cli plugins install ryantxu-ajax-panel
sudo systemctl restart grafana-server
```

## Step 4: Add Dashboard Variables (Optional but Recommended)

This allows you to switch between different symbols easily.

1. **Dashboard Settings** (⚙️ top right) → **Variables** → **Add variable**
2. Configure:
   - **Name**: `symbol`
   - **Type**: `Query`
   - **Data source**: `Market Data`
   - **Query**: 
     ```sql
     SHOW TAG VALUES FROM "market_data" WITH KEY = "symbol"
     ```
   - **Refresh**: On Dashboard Load
3. Click **Add**

4. Update your queries to use the variable:
   ```sql
   WHERE "symbol" = '$symbol' AND $timeFilter
   ```

## Step 5: Complete Candlestick Dashboard Example

Here's a complete dashboard JSON you can import:

1. Go to **Dashboards** → **Import**
2. Paste this JSON:

```json
{
  "dashboard": {
    "title": "Market Data - Candlestick",
    "panels": [
      {
        "title": "Price Chart",
        "type": "timeseries",
        "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0},
        "targets": [
          {
            "datasource": "Market Data",
            "query": "SELECT mean(\"open\") AS \"open\", mean(\"high\") AS \"high\", mean(\"low\") AS \"low\", mean(\"close\") AS \"close\" FROM \"market_data\" WHERE \"symbol\" = 'BTCUSDT' AND $timeFilter GROUP BY time($__interval) fill(previous)",
            "rawQuery": true,
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "line",
              "lineInterpolation": "linear",
              "fillOpacity": 10
            }
          }
        }
      },
      {
        "title": "Volume",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 12},
        "targets": [
          {
            "datasource": "Market Data",
            "query": "SELECT mean(\"volume\") AS \"volume\" FROM \"market_data\" WHERE \"symbol\" = 'BTCUSDT' AND $timeFilter GROUP BY time($__interval) fill(previous)",
            "rawQuery": true,
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "bars"
            }
          }
        }
      }
    ],
    "time": {"from": "now-7d", "to": "now"},
    "timezone": "browser",
    "refresh": "1m"
  }
}
```

## Step 6: Panel Styling for Better Candlestick Look

If using Time Series panel:

1. **Panel Options** (right sidebar):
   - Graph styles: Lines
   - Fill opacity: 0
   - Point size: 0

2. **Field Overrides**:
   - Close: Color = Green, Line width = 2
   - High: Color = Light green, Line style = Dots
   - Low: Color = Red, Line style = Dots

3. **Axis**:
   - Y-axis: Right side
   - Scale: Linear
   - Label: Price (USD)

## Useful InfluxQL Queries

### Get Latest Price
```sql
SELECT last("close") 
FROM "market_data" 
WHERE "symbol" = 'BTCUSDT'
```

### Get 24h Change
```sql
SELECT 
  (last("close") - first("close")) / first("close") * 100 AS "change_pct"
FROM "market_data" 
WHERE "symbol" = 'BTCUSDT' AND time > now() - 24h
```

### Get High/Low for Period
```sql
SELECT 
  max("high") AS "period_high",
  min("low") AS "period_low"
FROM "market_data" 
WHERE "symbol" = 'BTCUSDT' AND $timeFilter
```

### Multiple Symbols Comparison
```sql
SELECT mean("close") 
FROM "market_data" 
WHERE ("symbol" = 'BTCUSDT' OR "symbol" = 'ETHUSDT') AND $timeFilter
GROUP BY time($__interval), "symbol" fill(previous)
```

## Tips for Better Visualization

1. **Time Range**: Use appropriate time ranges
   - Short-term: Last 24 hours with 5m intervals
   - Medium-term: Last 7 days with 1h intervals
   - Long-term: Last 30 days with 4h intervals

2. **Auto Refresh**: Set to 1m or 5m for live data

3. **Annotations**: Add markers for important events

4. **Alerts**: Configure alerts for price thresholds

5. **Multiple Panels**: Create separate panels for:
   - Price chart (candlestick)
   - Volume bars
   - Technical indicators (if calculated)

## Troubleshooting

**No data showing?**
- Check time range matches your data
- Verify symbol name matches exactly (case-sensitive)
- Run query in InfluxDB CLI to verify data exists:
  ```sql
  USE market_data
  SELECT * FROM market_data WHERE symbol='BTCUSDT' ORDER BY time DESC LIMIT 5
  ```

**Data looks wrong?**
- Check `GROUP BY` interval - use `$__interval` for auto-adjustment
- Verify aggregation function (`mean`, `last`, etc.)

**Gaps in data?**
- Use `fill(previous)` or `fill(linear)` in GROUP BY clause
- Check data collection is running continuously
