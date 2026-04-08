import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from app.config import get_config
from app.db.connection import get_connection
from sqlalchemy import text


def create_candlestick_chart(symbol, data):
    """Create candlestick chart with indicators."""
    # Create subplots: candlestick + volume + indicators
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=('Candlestick with EMAs', 'Volume', 'RSI', 'BB Bands'),
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
    if 'ema_20' in data.columns:
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_20'], line=dict(color='blue', width=1), name='EMA 20'),
            row=1, col=1
        )

    if 'ema_50' in data.columns:
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_50'], line=dict(color='red', width=1), name='EMA 50'),
            row=1, col=1
        )

    if 'ema_200' in data.columns:
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['ema_200'], line=dict(color='green', width=1), name='EMA 200'),
            row=1, col=1
        )

    # Add Bollinger Bands
    if 'bb_upper' in data.columns:
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
    if 'rsi_14' in data.columns:
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['rsi_14'], line=dict(color='purple', width=1), name='RSI 14'),
            row=3, col=1
        )
        # Add RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # BB Position (instead of MACD for now to simplify)
    if 'bb_position' in data.columns:
        fig.add_trace(
            go.Scatter(x=data['trade_date'], y=data['bb_position'], line=dict(color='blue', width=1), name='BB Position'),
            row=4, col=1
        )
        fig.add_hline(y=1, line_dash="dash", line_color="red", row=4, col=1)
        fig.add_hline(y=-1, line_dash="dash", line_color="green", row=4, col=1)

    # Remove weekend gaps
    fig.update_xaxes(rangebreaks=[
        dict(bounds=["sat", "mon"]), # hide weekends
    ])

    # Update layout
    fig.update_layout(
        title=f'{symbol} Technical Analysis',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        height=800
    )

    return fig


def main():
    st.title("📊 Technical Analysis Dashboard")
    cfg = get_config()

    # Get available symbols
    available_symbols = []
    with get_connection() as conn:
        try:
            if cfg.postgres_url:
                query = text("SELECT DISTINCT symbol FROM fct_equity_features_1d ORDER BY symbol")
                res = conn.execute(query).fetchall()
                available_symbols = [r[0] for r in res]
            else:
                available_symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM fct_equity_features_1d ORDER BY symbol").fetchall()]
        except Exception:
            available_symbols = []

    if not available_symbols:
        st.warning("No technical analysis data available. Run the dbt pipeline from the Data Management page first.")
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
    with get_connection() as conn:
        if cfg.postgres_url:
            query = text("""
                SELECT * FROM fct_equity_features_1d
                WHERE symbol = :sym
                AND trade_date BETWEEN :start AND :end
                ORDER BY trade_date
            """)
            data = pd.read_sql(query, conn, params={
                "sym": selected_symbol,
                "start": start_date,
                "end": end_date
            })
        else:
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
        rsi_val = latest.get('rsi_14')
        st.metric("RSI 14", f"{rsi_val:.1f}" if pd.notna(rsi_val) else "N/A")
    with col4:
        bb_pos = latest.get('bb_position')
        st.metric("BB Position", f"{bb_pos:.2f}" if pd.notna(bb_pos) else "N/A")

    # Create and display chart
    fig = create_candlestick_chart(selected_symbol, data)
    st.plotly_chart(fig, use_container_width=True)

    # Technical indicators table
    st.subheader("📈 Technical Indicators")
    cols = ['trade_date', 'daily_close', 'ema_20', 'ema_50', 'rsi_14', 'bb_position']
    indicators_df = data[[c for c in cols if c in data.columns]].tail(10)
    st.dataframe(indicators_df, use_container_width=True)


if __name__ == "__main__":
    main()
