"""
Laklak - Cross-Platform Market Data Collector

Simple, unified API for collecting financial market data from multiple sources.

Basic Usage:
    >>> from laklak import Laklak
    >>> 
    >>> fetcher = Laklak()
    >>> fetcher.collect("BTCUSDT", exchange="bybit")
    >>> fetcher.collect("AAPL", exchange="yfinance")

Advanced Usage:
    >>> from laklak import collect, backfill
    >>> 
    >>> # Quick collection
    >>> collect("ETHUSDT", exchange="bybit")
    >>> 
    >>> # Historical backfill
    >>> backfill("BTCUSDT", exchange="bybit", days=30)
"""

__version__ = "1.0.9"
__author__ = "Eulex0x"
__license__ = "MIT"

from .core import Laklak, collect, backfill
from .exchanges import BybitExchange, DeribitExchange, YFinanceExchange

__all__ = [
    "Laklak",
    "collect",
    "backfill",
    "BybitExchange",
    "DeribitExchange",
    "YFinanceExchange",
]
