"""Basic tests for laklak package."""

import pytest


def test_import_laklak():
    """Test that laklak package can be imported."""
    import laklak
    assert laklak is not None


def test_import_core():
    """Test that laklak.core module can be imported."""
    from laklak import core
    assert core is not None


def test_import_exchanges():
    """Test that laklak.exchanges module can be imported."""
    from laklak import exchanges
    assert exchanges is not None


def test_config_import():
    """Test that config module can be imported."""
    import config
    assert config is not None
