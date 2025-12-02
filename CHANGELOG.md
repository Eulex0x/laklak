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
