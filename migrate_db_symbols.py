#!/usr/bin/env python3
"""
Database Migration Script - Rename Symbols to New Convention

This script migrates existing data in InfluxDB to use the new naming convention:
- Old: symbol='BTCUSDT', exchange='Bybit' → New: symbol='BTCUSDT_BYBIT'
- Old: symbol='BTCUSDT', exchange='Deribit', data_type='dvol' → New: symbol='BTC_DVOL'

Usage:
    python migrate_db_symbols.py --dry-run    # Preview changes without applying
    python migrate_db_symbols.py              # Apply migration
"""

import argparse
import logging
from influxdb import InfluxDBClient
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_migration")


class InfluxDBMigration:
    """Handles migration of InfluxDB data to new naming convention."""
    
    def __init__(self, dry_run=False):
        """Initialize the migration handler."""
        config = get_config()
        
        self.host = config.get("INFLUXDB_HOST", "192.168.4.2")
        self.port = config.get("INFLUXDB_PORT", 8086)
        self.database = config.get("INFLUXDB_DATABASE", "market_data")
        self.username = config.get("INFLUXDB_USERNAME", None)
        self.password = config.get("INFLUXDB_PASSWORD", None)
        self.dry_run = dry_run
        
        logger.info(f"Connecting to InfluxDB: {self.host}:{self.port}/{self.database}")
        
        self.client = InfluxDBClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database
        )
        
        # Test connection
        self.client.ping()
        logger.info("Successfully connected to InfluxDB")
    
    def get_existing_symbols(self):
        """Get all unique symbol+exchange combinations from the database."""
        query = '''
        SHOW TAG VALUES FROM "market_data" WITH KEY = "symbol"
        '''
        result = self.client.query(query)
        symbols = [point['value'] for point in result.get_points()]
        
        query_exchanges = '''
        SHOW TAG VALUES FROM "market_data" WITH KEY = "exchange"
        '''
        result_ex = self.client.query(query_exchanges)
        exchanges = [point['value'] for point in result_ex.get_points()]
        
        logger.info(f"Found {len(symbols)} unique symbols")
        logger.info(f"Found {len(exchanges)} unique exchanges: {exchanges}")
        
        return symbols, exchanges
    
    def get_symbol_exchange_pairs(self):
        """Get all unique symbol+exchange+data_type combinations."""
        # Get all unique combinations using SHOW TAG VALUES
        query_symbols = 'SHOW TAG VALUES FROM "market_data" WITH KEY = "symbol"'
        query_exchanges = 'SHOW TAG VALUES FROM "market_data" WITH KEY = "exchange"'
        query_datatypes = 'SHOW TAG VALUES FROM "market_data" WITH KEY = "data_type"'
        
        symbols = [p['value'] for p in self.client.query(query_symbols).get_points()]
        exchanges = [p['value'] for p in self.client.query(query_exchanges).get_points()]
        data_types = [p['value'] for p in self.client.query(query_datatypes).get_points()]
        
        logger.info(f"Found {len(symbols)} symbols, {len(exchanges)} exchanges, {len(data_types)} data types")
        
        # Now check which combinations actually exist
        pairs = []
        for symbol in symbols:
            for exchange in exchanges:
                for data_type in data_types:
                    # Check if this combination exists
                    check_query = f'''
                    SELECT COUNT(close) FROM "market_data" 
                    WHERE symbol = '{symbol}' AND exchange = '{exchange}' AND data_type = '{data_type}'
                    LIMIT 1
                    '''
                    result = self.client.query(check_query)
                    points = list(result.get_points())
                    
                    if points and points[0].get('count', 0) > 0:
                        pairs.append({
                            'old_symbol': symbol,
                            'exchange': exchange,
                            'data_type': data_type
                        })
        
        logger.info(f"Found {len(pairs)} unique symbol+exchange+data_type combinations")
        return pairs
    
    def calculate_new_symbol(self, old_symbol, exchange, data_type):
        """Calculate the new symbol name based on the naming convention."""
        
        # For Deribit DVOL data: extract base currency and use BASECURRENCY_DVOL
        if exchange.lower() == 'deribit' and data_type == 'dvol':
            base_currency = old_symbol.replace('USDT', '').replace('USDC', '').replace('USD', '')
            new_symbol = f"{base_currency}_DVOL"
        else:
            # For price data: SYMBOL_EXCHANGE
            exchange_suffix = exchange.upper().replace(' ', '')
            # Handle YFinance specifically
            if 'yfinance' in exchange.lower() or 'yahoo' in exchange.lower():
                exchange_suffix = 'YFINANCE'
            new_symbol = f"{old_symbol}_{exchange_suffix}"
        
        return new_symbol
    
    def migrate_data(self):
        """Perform the migration."""
        pairs = self.get_symbol_exchange_pairs()
        
        if not pairs:
            logger.warning("No data found to migrate")
            return
        
        migration_plan = []
        for pair in pairs:
            old_symbol = pair['old_symbol']
            exchange = pair['exchange']
            data_type = pair['data_type']
            
            new_symbol = self.calculate_new_symbol(old_symbol, exchange, data_type)
            
            # Skip if already in new format
            if '_' in old_symbol and (old_symbol.endswith('_BYBIT') or 
                                      old_symbol.endswith('_YFINANCE') or 
                                      old_symbol.endswith('_DVOL')):
                logger.info(f"✓ Already migrated: {old_symbol}")
                continue
            
            migration_plan.append({
                'old_symbol': old_symbol,
                'new_symbol': new_symbol,
                'exchange': exchange,
                'data_type': data_type
            })
        
        if not migration_plan:
            logger.info("✓ All data is already in the new format!")
            return
        
        logger.info(f"\n{'='*80}")
        logger.info("MIGRATION PLAN:")
        logger.info(f"{'='*80}")
        
        for i, plan in enumerate(migration_plan, 1):
            logger.info(f"{i}. {plan['old_symbol']} ({plan['exchange']}, {plan['data_type']}) → {plan['new_symbol']}")
        
        logger.info(f"{'='*80}\n")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info(f"Would migrate {len(migration_plan)} symbol combinations")
            return
        
        # Confirm before proceeding
        response = input(f"\nMigrate {len(migration_plan)} symbol combinations? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Migration cancelled by user")
            return
        
        # Perform migration
        for i, plan in enumerate(migration_plan, 1):
            try:
                self._migrate_single_symbol(plan, i, len(migration_plan))
            except Exception as e:
                logger.error(f"Failed to migrate {plan['old_symbol']}: {e}")
                continue
        
        logger.info("\n✓ Migration completed!")
    
    def _migrate_single_symbol(self, plan, current, total):
        """Migrate a single symbol."""
        old_symbol = plan['old_symbol']
        new_symbol = plan['new_symbol']
        exchange = plan['exchange']
        data_type = plan['data_type']
        
        logger.info(f"[{current}/{total}] Migrating: {old_symbol} → {new_symbol}")
        
        # Step 1: Copy data with new symbol tag
        select_query = f'''
        SELECT * FROM "market_data" 
        WHERE symbol = '{old_symbol}' AND exchange = '{exchange}' AND data_type = '{data_type}'
        '''
        
        result = self.client.query(select_query)
        points = list(result.get_points())
        
        if not points:
            logger.warning(f"  No data points found for {old_symbol}")
            return
        
        logger.info(f"  Found {len(points)} data points")
        
        # Process in batches to avoid "Request Entity Too Large" error
        BATCH_SIZE = 5000
        total_written = 0
        
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            
            # Create new points with updated symbol
            new_points = []
            for point in batch:
                new_point = {
                    "measurement": "market_data",
                    "tags": {
                        "symbol": new_symbol,
                        "exchange": exchange,
                        "data_type": data_type
                    },
                    "time": point['time'],
                    "fields": {
                        "open": point['open'],
                        "high": point['high'],
                        "low": point['low'],
                        "close": point['close'],
                        "volume": point['volume']
                    }
                }
                new_points.append(new_point)
            
            # Write batch
            self.client.write_points(new_points, time_precision='ms', batch_size=BATCH_SIZE)
            total_written += len(new_points)
            
            if len(points) > BATCH_SIZE:
                logger.info(f"  Progress: {total_written}/{len(points)} points written")
        
        logger.info(f"  ✓ Wrote {total_written} points with new symbol: {new_symbol}")
        
        # Step 2: Delete old data
        delete_query = f'''
        DELETE FROM "market_data" 
        WHERE symbol = '{old_symbol}' AND exchange = '{exchange}' AND data_type = '{data_type}'
        '''
        self.client.query(delete_query)
        logger.info(f"  ✓ Deleted old data for: {old_symbol}")
    
    def verify_migration(self):
        """Verify the migration was successful."""
        logger.info("\nVerifying migration...")
        
        symbols, exchanges = self.get_existing_symbols()
        
        logger.info("\nCurrent symbols in database:")
        for symbol in sorted(symbols):
            logger.info(f"  - {symbol}")
        
        # Check for old format symbols
        old_format = [s for s in symbols if '_' not in s]
        if old_format:
            logger.warning(f"\n⚠ Found {len(old_format)} symbols still in old format:")
            for symbol in old_format:
                logger.warning(f"  - {symbol}")
        else:
            logger.info("\n✓ All symbols are in the new format!")
    
    def close(self):
        """Close the database connection."""
        self.client.close()
        logger.info("Database connection closed")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description='Migrate InfluxDB symbols to new naming convention'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Only verify current state without migrating'
    )
    
    args = parser.parse_args()
    
    try:
        migrator = InfluxDBMigration(dry_run=args.dry_run)
        
        if args.verify:
            migrator.verify_migration()
        else:
            migrator.migrate_data()
            migrator.verify_migration()
        
        migrator.close()
        
    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
