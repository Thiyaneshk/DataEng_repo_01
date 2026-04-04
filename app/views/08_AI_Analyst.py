import streamlit as st
import requests
import json
import duckdb
import pandas as pd
from app.config import get_config


class OllamaClient:
    def __init__(self, base_url="http://ollama:11434"):
        self.base_url = base_url

    def generate(self, model, prompt, context=None):
        """Generate response from Ollama model."""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }

            if context:
                payload["context"] = context

            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def list_models(self):
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def get_stock_context(symbol, limit=10):
    """Get recent stock data for context."""
    cfg = get_config()
    try:
        with duckdb.connect(str(cfg.duckdb_path)) as conn:
            query = """
            SELECT trade_date, daily_close, daily_return_pct, ema_20, ema_50, rsi_14, macd_line, bb_position
            FROM fct_equity_features_1d
            WHERE symbol = ?
            ORDER BY trade_date DESC
            LIMIT ?
            """
            df = conn.execute(query, [symbol, limit]).df()

            if df.empty:
                return f"No data available for {symbol}"

            context = f"Recent data for {symbol}:\n"
            for _, row in df.iterrows():
                context += f"Date: {row['trade_date']}, Close: ${row['daily_close']:.2f}, "
                context += f"Return: {row['daily_return_pct']:.2f}%, "
                if pd.notna(row['rsi_14']):
                    context += f"RSI: {row['rsi_14']:.1f}, "
                if pd.notna(row['bb_position']):
                    context += f"BB Position: {row['bb_position']:.2f}, "
                context += "\n"

            return context
    except Exception as e:
        return f"Error retrieving data: {str(e)}"


def main():
    st.title("🤖 AI Stock Analyst (RAG)")

    # Initialize Ollama client
    ollama = OllamaClient()

    # Check available models
    models_response = ollama.list_models()
    if "error" in models_response:
        st.error(f"Cannot connect to Ollama: {models_response['error']}")
        st.info("Make sure Ollama is running: `docker-compose up ollama`")
        st.info("Pull a model: `docker-compose exec ollama ollama pull llama2`")
        return

    available_models = [model['name'] for model in models_response.get('models', [])]

    if not available_models:
        st.warning("No models available in Ollama.")
        st.info("Pull a model first: `docker-compose exec ollama ollama pull llama2`")
        return

    # Model selector
    selected_model = st.selectbox("Select AI Model", available_models)

    # Get available symbols
    cfg = get_config()
    try:
        with duckdb.connect(str(cfg.duckdb_path)) as conn:
            symbols_df = conn.execute("SELECT DISTINCT symbol FROM fct_equity_features_1d ORDER BY symbol").df()
            available_symbols = symbols_df['symbol'].tolist()
    except Exception:
        available_symbols = []

    if not available_symbols:
        st.warning("No stock data available. Run the ETL pipeline first.")
        return

    # Symbol selector
    selected_symbol = st.selectbox("Focus Symbol (optional)", ["General"] + available_symbols)

    # Chat interface
    st.subheader("💬 Ask the AI Analyst")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about stocks, technical analysis, or market insights..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare context
        context = ""
        if selected_symbol != "General":
            context = get_stock_context(selected_symbol)

        # Create enhanced prompt
        system_prompt = """You are an expert stock market analyst with deep knowledge of technical analysis, fundamental analysis, and market psychology.

You have access to real-time stock data including:
- Price data (open, high, low, close, volume)
- Technical indicators (RSI, MACD, Bollinger Bands, EMAs, Stochastic)
- Daily returns and market analysis

When analyzing stocks, consider:
- Technical signals and chart patterns
- Risk management and position sizing
- Market trends and sector analysis
- Fundamental factors when relevant

Provide clear, actionable insights based on the data available. Be honest about limitations and uncertainties in the market.

"""

        full_prompt = system_prompt
        if context:
            full_prompt += f"\nContext for {selected_symbol}:\n{context}\n"

        full_prompt += f"\nUser Question: {prompt}\n\nAnalysis:"

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = ollama.generate(selected_model, full_prompt)

            if "error" in response:
                st.error(f"Error: {response['error']}")
            else:
                ai_response = response.get("response", "No response generated")
                st.markdown(ai_response)

                # Add AI response to history
                st.session_state.messages.append({"role": "assistant", "content": ai_response})

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    # Model management section
    st.subheader("🔧 Model Management")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Available Models:**")
        for model in available_models:
            st.write(f"• {model}")

    with col2:
        st.write("**Pull New Model:**")
        new_model = st.text_input("Model name (e.g., llama2, mistral)")
        if st.button("Pull Model") and new_model:
            with st.spinner(f"Pulling {new_model}..."):
                # This would need to be run in a separate process
                st.info(f"To pull {new_model}, run: `docker-compose exec ollama ollama pull {new_model}`")


if __name__ == "__main__":
    main()