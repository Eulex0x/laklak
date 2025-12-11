"""
Configuration module for the market data collector.

This module provides a centralized configuration interface for the entire application.
You can easily modify settings in the SETTINGS section below, or use environment variables.
"""

from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================================
# ⚙️ SETTINGS - MODIFY THESE VALUES AS NEEDED
# ============================================================================
# Edit the values below to customize your data collection settings.
# These are the default values used if environment variables are not set.

SETTINGS = {
    # ═══════════════════════════════════════════════════════════════════════
    # API Configuration (for data fetching)
    # ═══════════════════════════════════════════════════════════════════════
    "API_KEY": None,                    # Your exchange API key (optional)
    "API_SECRET": None,                 # Your exchange API secret (optional)
    
    # ═══════════════════════════════════════════════════════════════════════
    # InfluxDB Configuration
    # ═══════════════════════════════════════════════════════════════════════
    "INFLUXDB_HOST": "192.168.4.2",       # InfluxDB server host
    "INFLUXDB_PORT": 8086,              # InfluxDB server port
    "INFLUXDB_DATABASE": "market_data", # Database name for storing data
    "INFLUXDB_USERNAME": None,          # InfluxDB username (optional)
    "INFLUXDB_PASSWORD": None,          # InfluxDB password (optional)
    "INFLUXDB_BATCH_SIZE": 2,           # Number of records per batch write
    
    # ═══════════════════════════════════════════════════════════════════════
    # Data Collection Configuration
    # ═══════════════════════════════════════════════════════════════════════
    "BASE_COIN": "BTC",                 # Base cryptocurrency (BTC, ETH, etc.)
    "DAYS": 10.0,                       # Days of historical data to fetch
                                        # Supports fractional values: 0.042 = 1 hour
    "RESOLUTION_KLINE": 60,             # Kline/Candle resolution in minutes (60 = 1 hour)
    "RESOLUTION_IV": 60,                # IV resolution in minutes (60 = 1 hour)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Logging Configuration
    # ═══════════════════════════════════════════════════════════════════════
    "LOG_LEVEL": "INFO",                # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "LOG_FILE": "logs/collector.log",   # Path to log file
}

# ============================================================================
# Configuration Loading (Environment Variables Override Settings)
# ============================================================================
# Environment variables take precedence over the SETTINGS defined above.
# This allows for flexible deployment without code changes.

API_KEY = os.getenv("API_KEY", SETTINGS["API_KEY"])
API_SECRET = os.getenv("API_SECRET", SETTINGS["API_SECRET"])

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST", SETTINGS["INFLUXDB_HOST"])
INFLUXDB_PORT = int(os.getenv("INFLUXDB_PORT", SETTINGS["INFLUXDB_PORT"]))
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE", SETTINGS["INFLUXDB_DATABASE"])
INFLUXDB_USERNAME = os.getenv("INFLUXDB_USERNAME", SETTINGS["INFLUXDB_USERNAME"])
INFLUXDB_PASSWORD = os.getenv("INFLUXDB_PASSWORD", SETTINGS["INFLUXDB_PASSWORD"])
INFLUXDB_BATCH_SIZE = int(os.getenv("INFLUXDB_BATCH_SIZE", SETTINGS["INFLUXDB_BATCH_SIZE"]))

BASE_COIN = os.getenv("BASE_COIN", SETTINGS["BASE_COIN"])
DAYS = float(os.getenv("DAYS", SETTINGS["DAYS"]))
RESOLUTION_KLINE = int(os.getenv("RESOLUTION_KLINE", SETTINGS["RESOLUTION_KLINE"]))
RESOLUTION_IV = int(os.getenv("RESOLUTION_IV", SETTINGS["RESOLUTION_IV"])) * 60  # Convert to seconds

LOG_LEVEL = os.getenv("LOG_LEVEL", SETTINGS["LOG_LEVEL"])
LOG_FILE = os.getenv("LOG_FILE", SETTINGS["LOG_FILE"])


def get_config():
    """
    Return a dictionary of all configuration values.
    
    This function provides a centralized interface for accessing configuration
    throughout the application.
    
    Returns:
        dict: Configuration dictionary with all settings
    """
    return {
        # API Configuration
        "API_KEY": API_KEY,
        "API_SECRET": API_SECRET,
        
        # InfluxDB Configuration
        "INFLUXDB_HOST": INFLUXDB_HOST,
        "INFLUXDB_PORT": INFLUXDB_PORT,
        "INFLUXDB_DATABASE": INFLUXDB_DATABASE,
        "INFLUXDB_USERNAME": INFLUXDB_USERNAME,
        "INFLUXDB_PASSWORD": INFLUXDB_PASSWORD,
        "INFLUXDB_BATCH_SIZE": INFLUXDB_BATCH_SIZE,
        
        # Data Collection Configuration
        "BASE_COIN": BASE_COIN,
        "DAYS": DAYS,
        "RESOLUTION_KLINE": RESOLUTION_KLINE,
        "RESOLUTION_IV": RESOLUTION_IV,
        
        # Logging Configuration
        "LOG_LEVEL": LOG_LEVEL,
        "LOG_FILE": LOG_FILE,
    }


def print_config():
    """Print all configuration values (useful for debugging)."""
    config = get_config()
    print("\n" + "="*80)
    print("CURRENT CONFIGURATION")
    print("="*80)
    for key, value in config.items():
        # Mask sensitive values
        if "PASSWORD" in key or "SECRET" in key or "KEY" in key:
            display_value = "***MASKED***" if value else None
        else:
            display_value = value
        print(f"{key:.<40} {display_value}")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_config()
