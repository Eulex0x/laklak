# Changelog

All notable changes to Laklak will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-02

### Added
- 🎉 Initial release of Laklak
- Multi-exchange support: Bybit, Deribit, Yahoo Finance
- Simple API: `from laklak import collect`
- InfluxDB time-series storage integration
- Automatic data validation and error handling
- Configurable batch processing
- Historical data backfill capability
- Comprehensive documentation and guides
- Production-ready logging system
- MIT License

### Supported Features
- OHLCV data collection (1-hour candles)
- Volatility index (DVOL) from Deribit
- Multi-asset support: crypto, stocks, indices, forex, commodities
- Grafana-ready data storage
- Scalable architecture (2 to 1000+ assets)

### Documentation
- Complete README with examples
- Multi-exchange configuration guide
- Grafana setup guide
- Quick reference guide
- Publishing guide for PyPI

## [1.0.7] - 2024-12-02

### Added
- ⭐ **Data Return Mode**: `collect()` and `backfill()` now return pandas DataFrames when `use_influxdb=False`
  - Returns `Dict[str, pd.DataFrame]` mapping symbol to OHLCV data
  - Enables usage without InfluxDB dependency
  - Perfect for research, ML pipelines, and ad-hoc analysis

### Changed
- Updated return type annotations to `Union[bool, Dict[str, pd.DataFrame]]`
- Enhanced documentation with DataFrame usage examples
- Added imports for `Dict` and `pandas` in core module

### Examples
```python
# Get data as DataFrame instead of writing to InfluxDB
data = collect('BTCUSDT', exchange='bybit', timeframe='1h', period=30, use_influxdb=False)
btc_df = data['BTCUSDT']  # pandas DataFrame with OHLCV columns
print(btc_df.head())
```

## [1.0.6] - 2024-12-02

### Fixed
- Made InfluxDB optional via `use_influxdb` parameter
- Removed all `config.py` dependencies
- All modules now use `os.getenv()` directly for environment variables

## [1.0.5] - 2024-12-02

### Fixed
- Additional import fixes for exchange modules

## [1.0.4] - 2024-12-02

### Fixed
- Removed config.py imports from all exchange modules
- Fixed import errors in Bybit and Deribit modules

## [1.0.3] - 2024-12-02

### Fixed
- Added `laklak` module to packages list in setup.py and pyproject.toml
- Fixed ModuleNotFoundError when importing from package

## [1.0.2] - 2024-12-02

### Fixed
- Package import issues

## [1.0.1] - 2024-12-02

### Fixed
- Initial package structure fixes

## [Unreleased]

### Planned for v1.1.0
- Real-time WebSocket streaming
- Additional exchange support (Binance, Kraken)
- Multi-timeframe data collection (5m, 15m, 4h, 1d)
- Built-in technical indicators
- Enhanced error recovery

### Planned for v2.0.0
- Breaking API changes for consistency
- Cloud-native deployment options
- Plugin architecture for custom exchanges
- Web UI for monitoring
