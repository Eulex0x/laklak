"""
Laklak - Cross-Platform Market Data Collector
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='laklak',
    version='1.0.9',
    author='Eulex0x',
    author_email='milad@safda.de',
    description='Cross-Platform Market Data Collector',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Eulex0x/laklak',
    project_urls={
        'Bug Reports': 'https://github.com/Eulex0x/laklak/issues',
        'Source': 'https://github.com/Eulex0x/laklak',
        'Documentation': 'https://github.com/Eulex0x/laklak#readme',
    },
    packages=['laklak', 'modules', 'modules.exchanges'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=22.0',
            'flake8>=5.0',
            'mypy>=0.990',
        ],
    },
    entry_points={
        'console_scripts': [
            'laklak-collect=data_collector:main',
            'laklak-backfill=backfill:main',
        ],
    },
    include_package_data=True,
    keywords='trading finance data crypto stocks forex bybit deribit yfinance influxdb market-data',
    zip_safe=False,
)
