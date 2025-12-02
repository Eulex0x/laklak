#!/usr/bin/env python3
"""
Cleanup script to remove duplicate old-format data after partial migration.
"""

import logging
from influxdb import InfluxDBClient
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cleanup")

def cleanup_duplicates():
    """Remove old-format symbols that have been successfully migrated."""
    config = get_config()
    
    client = InfluxDBClient(
        host=config.get("INFLUXDB_HOST", "localhost"),
        port=config.get("INFLUXDB_PORT", 8086),
        username=config.get("INFLUXDB_USERNAME", None),
        password=config.get("INFLUXDB_PASSWORD", None),
        database=config.get("INFLUXDB_DATABASE", "market_data")
    )
    
    logger.info("Connected to InfluxDB")
    
    # List of all symbols to clean up (old format that have been migrated)
    # Get all old-format symbols and remove them
    query = 'SHOW TAG VALUES FROM "market_data" WITH KEY = "symbol"'
    result = client.query(query)
    all_symbols = [p['value'] for p in result.get_points()]
    
    # Filter to only old-format symbols (without underscore)
    old_symbols = [s for s in all_symbols if '_' not in s]
    
    logger.info(f"\nFound {len(old_symbols)} old-format symbols to clean up")
    
    # For each old symbol, delete all data (all exchanges and data types)
    migrated_pairs = []
    for symbol in old_symbols:
        migrated_pairs.append((symbol, 'Bybit', 'kline'))
        migrated_pairs.append((symbol, 'Deribit', 'dvol'))
    
    logger.info(f"\nCleaning up {len(migrated_pairs)} successfully migrated symbols...")
    
    for old_symbol, exchange, data_type in migrated_pairs:
        logger.info(f"Removing old data for: {old_symbol} ({exchange}, {data_type})")
        
        delete_query = f'''
        DELETE FROM "market_data" 
        WHERE symbol = '{old_symbol}' AND exchange = '{exchange}' AND data_type = '{data_type}'
        '''
        client.query(delete_query)
        logger.info(f"  ✓ Deleted")
    
    logger.info("\n✓ Cleanup completed!")
    client.close()

if __name__ == "__main__":
    cleanup_duplicates()
