import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import duckdb
import pandas as pd
from app.config import get_config


def create_candlestick_chart(symbol, data):
    """Create candlestick chart with indicators."""
    # Create subplots: candlestick + volume + indicators
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Candlestick with EMAs', 'Volume', 'RSI', 'MACD'),
        row_heights=[0.5, 0.15, 0.15, 0.2]
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data['trade_date'],
            open=data['daily_open'],
            high=data['daily_high'],
            low=data['daily_low'],
            close=data['daily_close'],
            name='Candlestick'
        ),
        row=1, col=1
    )

    # Add EMAs
    if 'ema_20' in data.columns and data['ema_20'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_20'], line=dict(color='blue', width=1), name='EMA 20'),
            row=1, col=1
        )

    if 'ema_50' in data.columns and data['ema_50'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_50'], line=dict(color='red', width=1), name='EMA 50'),
            row=1, col=1
        )

    if 'ema_200' in data.columns and data['ema_200'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_200'], line=dict(color='green', width=1), name='EMA 200'),
            row=1, col=1
        )

    # Add Bollinger Bands
    if 'bb_upper' in data.columns and data['bb_upper'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['bb_upper'], line=dict(color='gray', width=1, dash='dot'), name='BB Upper'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['bb_middle'], line=dict(color='orange', width=1, dash='dash'), name='BB Middle'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['bb_lower'], line=dict(color='gray', width=1, dash='dot'), name='BB Lower'),
            row=1, col=1
        )

    # Volume chart
    colors = ['red' if row['daily_open'] > row['daily_close'] else 'green' for index, row in data.iterrows()]
    fig.add_trace(
        go.Bar(x=data['trade_date'], y=data['daily_volume'], marker_color=colors, name='Volume'),
        row=2, col=1
    )

    # RSI
    if 'rsi_14' in data.columns and data['rsi_14'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['rsi_14'], line=dict(color='purple', width=1), name='RSI 14'),
            row=3, col=1
        )
        # Add RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # MACD
    if 'macd_line' in data.columns and data['macd_line'].notna().any():
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['macd_line'], line=dict(color='blue', width=1), name='MACD'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['signal_line'], line=dict(color='red', width=1), name='Signal'),
            row=4, col=1
        )
        colors = ['red' if val < 0 else 'green' for val in data['macd_histogram']]
        fig.add_trace(
            go.Bar(x=data['trade_date'], y=data['macd_histogram'], marker_color=colors, name='Histogram'),
            row=4, col=1
        )

    # Update layout
    fig.update_layout(
        title=f'{symbol} Technical Analysis',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        height=800
    )

    # Update y-axes
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig


def main():
    st.title("📊 Technical Analysis Dashboard")
    cfg = get_config()

    # Get available symbols
    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        try:
            symbols_df = conn.execute("SELECT DISTINCT symbol FROM fct_equity_features_1d ORDER BY symbol").df()
            available_symbols = symbols_df['symbol'].tolist()
        except Exception:
            available_symbols = []

    if not available_symbols:
        st.warning("No technical analysis data available. Run the dbt pipeline first.")
        return

    # Symbol selector
    selected_symbol = st.selectbox("Select Symbol", available_symbols)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=pd.to_datetime('2024-01-01'))
    with col2:
        end_date = st.date_input("End Date", value=pd.to_datetime('today'))

    # Fetch data
    with duckdb.connect(str(cfg.duckdb_path)) as conn:
        query = """
        SELECT * FROM fct_equity_features_1d
        WHERE symbol = ?
        AND trade_date BETWEEN ? AND ?
        ORDER BY trade_date
        """
        data = conn.execute(query, [selected_symbol, start_date, end_date]).df()

    if data.empty:
        st.warning(f"No data available for {selected_symbol} in the selected date range.")
        return

    # Display key metrics
    latest = data.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Latest Close", f"${latest['daily_close']:.2f}")
    with col2:
        st.metric("Daily Return", f"{latest['daily_return_pct']:.2f}%")
    with col3:
        rsi_val = latest.get('rsi_14', 'N/A')
        st.metric("RSI 14", f"{rsi_val:.1f}" if pd.notna(rsi_val) else "N/A")
    with col4:
        bb_pos = latest.get('bb_position', 'N/A')
        st.metric("BB Position", f"{bb_pos:.2f}" if pd.notna(bb_pos) else "N/A")

    # Create and display chart
    fig = create_candlestick_chart(selected_symbol, data)
    st.plotly_chart(fig, use_container_width=True)

    # Technical indicators table
    st.subheader("📈 Technical Indicators")
    indicators_df = data[['trade_date', 'daily_close', 'ema_20', 'ema_50', 'rsi_14', 'macd_line', 'bb_position', 'stoch_k']].tail(10)
    st.dataframe(indicators_df, use_container_width=True)

    # Analysis summary
    st.subheader("🔍 Analysis Summary")

    # Simple analysis logic
    analysis = []

    if pd.notna(latest.get('rsi_14')):
        rsi = latest['rsi_14']
        if rsi > 70:
            analysis.append("⚠️ RSI indicates overbought conditions")
        elif rsi < 30:
            analysis.append("✅ RSI indicates oversold conditions")

    if pd.notna(latest.get('bb_position')):
        bb_pos = latest['bb_position']
        if bb_pos > 1:
            analysis.append("📈 Price above upper Bollinger Band")
        elif bb_pos < -1:
            analysis.append("📉 Price below lower Bollinger Band")

    if pd.notna(latest.get('macd_histogram')):
        macd_hist = latest['macd_histogram']
        if macd_hist > 0:
            analysis.append("📊 MACD histogram positive (bullish momentum)")
        else:
            analysis.append("📊 MACD histogram negative (bearish momentum)")

    if analysis:
        for item in analysis:
            st.write(item)
    else:
        st.write("📋 No significant technical signals detected")


if __name__ == "__main__":
    main()