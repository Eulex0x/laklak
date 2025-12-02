# How to Publish Laklak to PyPI

This guide walks you through publishing Laklak to PyPI so anyone can install it with `pip install laklak`.

## Prerequisites

1. **PyPI Account**: Create accounts on both [Test PyPI](https://test.pypi.org) and [PyPI](https://pypi.org)
2. **API Tokens**: Generate API tokens from your account settings
3. **Build Tools**: Install required packages

```bash
pip install build twine
```

## Step 1: Update Version

Edit `setup.py` and `pyproject.toml` to update the version number:

```python
version='1.0.0'  # Change to new version
```

## Step 2: Build the Package

```bash
# Clean previous builds
rm -rf build dist *.egg-info

# Build distribution packages
python -m build
```

This creates:
- `dist/laklak-1.0.0.tar.gz` (source distribution)
- `dist/laklak-1.0.0-py3-none-any.whl` (wheel distribution)

## Step 3: Test on Test PyPI (Recommended)

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ --no-deps laklak
```

## Step 4: Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*
```

Enter your PyPI username and API token when prompted.

## Step 5: Verify Installation

```bash
# Install from PyPI
pip install laklak

# Test the import
python -c "from laklak import collect; print('Success!')"
```

## Using API Tokens (Recommended)

Create `~/.pypirc` with your API tokens:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-API-TOKEN-HERE
```

**Important**: Keep this file secure! Never commit it to version control.

```bash
chmod 600 ~/.pypirc
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to your GitHub repository secrets.

## Version Management

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0 → 2.0.0): Breaking changes
- **MINOR** version (1.0.0 → 1.1.0): New features, backwards compatible
- **PATCH** version (1.0.0 → 1.0.1): Bug fixes

## Pre-release Checklist

- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] Version number incremented
- [ ] README examples work
- [ ] Dependencies are correct in requirements.txt
- [ ] License file is included

## Post-release

1. **Tag the release** in Git:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

2. **Create GitHub Release** with release notes

3. **Announce** on relevant channels:
   - GitHub Discussions
   - Twitter/X
   - Reddit (r/Python, r/algotrading)
   - Dev.to

## Troubleshooting

### "Package already exists"
- You cannot re-upload the same version
- Increment the version number and rebuild

### "Invalid distribution"
- Check `setup.py` for syntax errors
- Ensure all required files are included in MANIFEST.in

### "Authentication failed"
- Verify API token is correct
- Check `.pypirc` permissions: `chmod 600 ~/.pypirc`

### "Missing dependencies"
- Test installation in a fresh virtual environment
- Verify all dependencies are listed in `requirements.txt`

## Quick Commands Reference

```bash
# Build
python -m build

# Test PyPI
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*

# Install locally for testing
pip install -e .

# Clean build artifacts
rm -rf build dist *.egg-info
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Documentation](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
