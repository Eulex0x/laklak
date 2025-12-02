# Quick Start: Publish to PyPI in 5 Minutes

```bash
# 1. Install build tools
pip install build twine

# 2. Build the package
python -m build

# 3. Upload to PyPI
twine upload dist/*
```

Done! Now anyone can:

```bash
pip install laklak
```

And use it like:

```python
from laklak import collect

collect("BTCUSDT", exchange="bybit")
collect("AAPL", exchange="yfinance")
```

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.
