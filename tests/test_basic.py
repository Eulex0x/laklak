"""Basic tests for laklak package."""

import sys
import os


def test_python_version():
    """Test that Python version is correct."""
    assert sys.version_info >= (3, 7)


def test_modules_exist():
    """Test that required module files exist."""
    base_path = os.path.dirname(os.path.dirname(__file__))
    
    assert os.path.exists(os.path.join(base_path, "laklak", "__init__.py"))
    assert os.path.exists(os.path.join(base_path, "laklak", "core.py"))
    assert os.path.exists(os.path.join(base_path, "modules", "exchanges", "bybit.py"))
    assert os.path.exists(os.path.join(base_path, "config.py"))
    assert os.path.exists(os.path.join(base_path, "data_collector.py"))


def test_requirements_file():
    """Test that requirements.txt exists and has content."""
    base_path = os.path.dirname(os.path.dirname(__file__))
    req_file = os.path.join(base_path, "requirements.txt")
    
    assert os.path.exists(req_file)
    with open(req_file, 'r') as f:
        content = f.read()
        assert len(content) > 0
        assert "requests" in content
        assert "pandas" in content
