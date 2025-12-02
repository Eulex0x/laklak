"""
Configuration module for the market data collector.

This module loads configuration from environment variables and provides
a centralized configuration interface for the entire application.
"""

from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================================
# API Configuration (for data fetching)
# ============================================================================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# ============================================================================
# InfluxDB Configuration (1.6)
# ============================================================================
INFLUXDB_HOST = os.getenv("INFLUXDB_HOST", "localhost")
INFLUXDB_PORT = int(os.getenv("INFLUXDB_PORT", 8086))
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE", "market_data")
INFLUXDB_USERNAME = os.getenv("INFLUXDB_USERNAME", None)
INFLUXDB_PASSWORD = os.getenv("INFLUXDB_PASSWORD", None)
INFLUXDB_BATCH_SIZE = int(os.getenv("INFLUXDB_BATCH_SIZE", 2))  # Start with 2, upgrade as needed

# ============================================================================
# Data Collection Configuration
# ============================================================================
BASE_COIN = os.getenv("BASE_COIN", "BTC")
DAYS = float(os.getenv("DAYS", 10))  # Support fractional days (e.g., 0.042 = 1 hour)
RESOLUTION_KLINE = int(os.getenv("RESOLUTION_KLINE", 60))  # 60 for 1 hour
RESOLUTION_IV = int(os.getenv("RESOLUTION_IV", 60)) * 60  # Convert to seconds

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/collector.log")


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
