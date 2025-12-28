"""
Exchanges module - Contains data providers for various exchanges and data sources.
"""

from .bybit import BybitKline
from .deribit import DeribitDVOL

# YFinance uses Python 3.10+ type hints (union with |) which breaks on 3.9
try:
    from .yfinance import YFinanceKline
    __all__ = ['BybitKline', 'DeribitDVOL', 'YFinanceKline']
except (ImportError, TypeError):
    # Python 3.9 compatibility - yfinance not available
    __all__ = ['BybitKline', 'DeribitDVOL']
