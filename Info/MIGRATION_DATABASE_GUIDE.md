# Database Migration Guide

This guide explains how to migrate your existing InfluxDB data to the new naming convention.

## What Changes?

### Old Format:
- Symbol: `BTCUSDT`, Exchange: `Bybit`, Data Type: `kline`
- Symbol: `BTCUSDT`, Exchange: `Deribit`, Data Type: `dvol`

### New Format:
- `BTCUSDT_BYBIT` (price data)
- `BTC_DVOL` (volatility data)

## Migration Steps

### 1. Verify Current State (Optional)

First, check what data you have in the database:

```bash
python migrate_db_symbols.py --verify
```

This shows all symbols currently in your database without making any changes.

### 2. Preview Migration (Dry Run)

See what changes will be made WITHOUT actually applying them:

```bash
python migrate_db_symbols.py --dry-run
```

This will show you:
- Which symbols will be renamed
- How many data points will be affected
- The new symbol names

### 3. Run Migration

Once you're ready, run the actual migration:

```bash
python migrate_db_symbols.py
```

The script will:
1. Show you the migration plan
2. Ask for confirmation (type `yes` to proceed)
3. Copy data with new symbol names
4. Delete old data
5. Verify the migration was successful

## Example Output

```
================================================================================
MIGRATION PLAN:
================================================================================
1. BTCUSDT (Bybit, kline) → BTCUSDT_BYBIT
2. BTCUSDT (Deribit, dvol) → BTC_DVOL
3. ETHUSDT (Bybit, kline) → ETHUSDT_BYBIT
4. ETHUSDT (Deribit, dvol) → ETH_DVOL
5. SOLUSDT (Bybit, kline) → SOLUSDT_BYBIT
================================================================================

Migrate 5 symbol combinations? (yes/no):
```

## What the Script Does

1. **Queries** your database for all unique symbol+exchange+data_type combinations
2. **Calculates** the new symbol name based on the naming convention:
   - Price data: `SYMBOL_EXCHANGE` (e.g., `BTCUSDT_BYBIT`)
   - Volatility data: `BASECURRENCY_DVOL` (e.g., `BTC_DVOL`)
3. **Copies** all data points with the new symbol tag
4. **Deletes** the old data points
5. **Verifies** the migration completed successfully

## Safety Features

- ✅ **Dry-run mode**: Preview changes without applying them
- ✅ **Confirmation prompt**: Must type "yes" to proceed
- ✅ **Error handling**: Continues if one symbol fails
- ✅ **Verification**: Checks migration success at the end
- ✅ **Non-destructive**: Creates new points before deleting old ones

## Rollback

If something goes wrong, you can:

1. **Before migration**: The script doesn't modify data in dry-run mode
2. **During migration**: Press Ctrl+C to stop (partially migrated data will remain)
3. **After migration**: Restore from InfluxDB backup if you made one

## Backup Recommendation

**IMPORTANT**: Always backup your database before migration:

```bash
# Backup InfluxDB database
influxd backup -portable -database market_data /path/to/backup/

# Restore if needed
influxd restore -portable -db market_data /path/to/backup/
```

## Command Reference

```bash
# Preview changes only (no modifications)
python migrate_db_symbols.py --dry-run

# Check current database state
python migrate_db_symbols.py --verify

# Run the actual migration
python migrate_db_symbols.py
```

## After Migration

Once migrated, your queries should use the new symbol names:

```sql
-- Old query
SELECT * FROM market_data WHERE symbol = 'BTCUSDT' AND exchange = 'Bybit'

-- New query
SELECT * FROM market_data WHERE symbol = 'BTCUSDT_BYBIT'
```

## Troubleshooting

### "No data found to migrate"
- Your database is empty or already migrated
- Check with `--verify` to see current symbols

### "Already migrated: BTCUSDT_BYBIT"
- That symbol is already in the new format
- Script automatically skips it

### Migration fails for a symbol
- Script logs the error and continues with remaining symbols
- Check logs for details
- You can re-run the script safely (it skips already-migrated symbols)

## Grafana Dashboards

After migration, update your Grafana queries:

**Old:**
```sql
SELECT mean("close") FROM "market_data" 
WHERE symbol = 'BTCUSDT' AND exchange = 'Bybit'
```

**New:**
```sql
SELECT mean("close") FROM "market_data" 
WHERE symbol = 'BTCUSDT_BYBIT'
```

Or use pattern matching for flexibility:
```sql
SELECT mean("close") FROM "market_data" 
WHERE symbol =~ /^BTCUSDT_/
GROUP BY symbol
```
