import logging
import pandas as pd
from config import get_config
config = get_config()

def apply_power_ma(df_kline, df_iv, window=config['IV_AVERAGE_PERIOD']):
    logging.info("Applying Power Moving Average and identifying fractal points in IV data.") 
    df_iv['high'] = df_iv['high'].astype(float)
    df_iv['low'] = df_iv['low'].astype(float)
    df_iv['open'] = df_iv['open'].astype(float)
    df_iv['close'] = df_iv['close'].astype(float)
    df_iv['candle_range_pct'] = ((df_iv['high'] - df_iv['low']) / df_iv['low']) * 100
    df_iv['avg_candle_range'] = df_iv['candle_range_pct'].rolling(window).mean()
    df_iv['is_green'] = df_iv['close'] > df_iv['open']
    df_iv['is_fractal'] = (
        df_iv['is_green'] & 
        ((((df_iv['close'] - df_iv['open']) / df_iv['open']) * 100 ) > df_iv['avg_candle_range']) & ((((df_iv['close'] - df_iv['open']) / df_iv['open']) * 100 ) > 1)
    )
    logging.info(f"Fractal points identified in IV data: {df_iv['is_fractal'].sum()} out of {len(df_iv)}")
    
    # Prepare kline data
    df_kline['high'] = df_kline['high'].astype(float)
    df_kline['low'] = df_kline['low'].astype(float)
    df_kline['open'] = df_kline['open'].astype(float)
    df_kline['close'] = df_kline['close'].astype(float)
    
    # Calculate price change percentage for each kline candle (close to close)
    df_kline['price_change_pct'] = df_kline['close'].pct_change() * 100
    df_kline['abs_price_change_pct'] = df_kline['price_change_pct'].abs()
    
    # Calculate rolling average of price changes in kline
    df_kline['avg_price_change'] = df_kline['abs_price_change_pct'].rolling(window).mean()
    
    # Get fractal times from IV data
    fractal_times = set(df_iv[df_iv['is_fractal']]['time'])
    
    # Create two signal types:
    # 1. DIVERGENCE: IV shock + LOW price movement (PREMIUM SELLING OPPORTUNITY)
    df_kline['iv_divergence'] = (
        df_kline['time'].isin(fractal_times) & 
        (df_kline['abs_price_change_pct'] < df_kline['avg_price_change'])
    )
    
    # 2. CONFIRMATION: IV shock + HIGH price movement (GENUINE VOLATILITY)
    df_kline['iv_confirmation'] = (
        df_kline['time'].isin(fractal_times) & 
        (df_kline['abs_price_change_pct'] >= df_kline['avg_price_change'])
    )
    
    # Combined fractal marker (for backward compatibility)
    df_kline['iv_fractal'] = df_kline['time'].isin(fractal_times)
    
    logging.info(f"IV Fractal Analysis:")
    logging.info(f"  Total IV fractals: {len(fractal_times)}")
    logging.info(f"  Divergence signals (IV high, Price low): {df_kline['iv_divergence'].sum()}")
    logging.info(f"  Confirmation signals (IV high, Price high): {df_kline['iv_confirmation'].sum()}")
    
    return df_iv, df_kline