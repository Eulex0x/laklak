import logging
import pandas as pd
import plotly.graph_objects as go
from modules.iv_shock import apply_power_ma

def fetch_and_plot_iv_interactive(df_kline: pd.DataFrame, df_iv: pd.DataFrame) -> tuple:
    # Apply fractal detection and transfer to kline
    df_iv, df_kline = apply_power_ma(df_kline, df_iv)
    
    # Convert to float
    df_kline['close'] = df_kline['close'].astype(float)
    df_kline['open'] = df_kline['open'].astype(float)
    df_kline['high'] = df_kline['high'].astype(float)
    df_kline['low'] = df_kline['low'].astype(float)
    
    df_iv['close'] = df_iv['close'].astype(float)
    df_iv['open'] = df_iv['open'].astype(float)
    df_iv['high'] = df_iv['high'].astype(float)
    df_iv['low'] = df_iv['low'].astype(float)

    # Create single main chart
    fig = go.Figure()

    # === BTC Price Candlestick ===
    fig.add_trace(go.Candlestick(
        x=df_kline['time'],
        open=df_kline['open'],
        high=df_kline['high'],
        low=df_kline['low'],
        close=df_kline['close'],
        name='BTC Price',
        showlegend=False,
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350',
        increasing_fillcolor='#26a69a',
        decreasing_fillcolor='#ef5350'
    ))
    
    # Mark DIVERGENCE signals - IV High + Price Low (BEST OPPORTUNITY)
    divergence_points = df_kline[df_kline['iv_divergence']]
    fig.add_trace(go.Scatter(
        x=divergence_points['time'],
        y=divergence_points['low'] * 0.995,  # Place below candle
        mode='markers+text',
        name='Premium Selling Signal',
        marker=dict(
            symbol='triangle-up', 
            size=18, 
            color='#FFD700',
            line=dict(color='#FF4500', width=2)
        ),
        text=['💰'] * len(divergence_points),
        textposition='bottom center',
        textfont=dict(size=20),
        showlegend=True
    ))

    # Update layout with beautiful styling
    fig.update_layout(
        title={
            'text': '💹 BTC Premium Selling Opportunities (Strangle Strategy)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2c3e50'}
        },
        hovermode='x unified',
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#2c3e50',
            borderwidth=1,
            font=dict(size=14)
        ),
        # Enable range slider and selector for interactive zooming
        xaxis=dict(
            title='Time',
            rangeslider=dict(
                visible=True,
                thickness=0.05,
                bgcolor='rgba(38, 166, 154, 0.1)'
            ),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1h", step="hour", stepmode="backward"),
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor='rgba(255, 255, 255, 0.9)',
                activecolor='rgba(255, 215, 0, 0.5)',
                bordercolor='#2c3e50',
                borderwidth=1,
                x=0,
                y=1.12
            ),
            showgrid=True,
            gridcolor='rgba(189, 195, 199, 0.3)'
        ),
        yaxis=dict(
            title='Price (USD)',
            showgrid=True,
            gridcolor='rgba(189, 195, 199, 0.3)',
            side='right'
        ),
        # Professional dark background
        plot_bgcolor='#ffffff',
        paper_bgcolor='#f8f9fa',
        # Make charts responsive to window size
        autosize=True,
        # Enable drag to zoom and pan
        dragmode='zoom',
        # Add annotation with signal count
        annotations=[
            dict(
                text=f'Signals Found: {len(divergence_points)}',
                xref='paper', yref='paper',
                x=0.02, y=0.98,
                showarrow=False,
                font=dict(size=16, color='#FF4500'),
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#FF4500',
                borderwidth=2,
                borderpad=8
            )
        ]
    )
    
    fig.show()

    return df_iv, df_kline




    
