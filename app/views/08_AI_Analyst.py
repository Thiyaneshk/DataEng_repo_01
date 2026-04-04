import streamlit as st
import requests
import json
import duckdb
import pandas as pd
from app.config import get_config


class OllamaClient:
    def __init__(self, base_url=None):
        if base_url is None:
            # Auto-detect environment
            if self._is_running_in_docker():
                self.base_url = "http://ollama:11434"
            else:
                self.base_url = "http://localhost:11434"
        else:
            self.base_url = base_url

    def _is_running_in_docker(self):
        """Check if running inside a Docker container."""
        try:
            with open('/.dockerenv', 'r'):
                return True
        except FileNotFoundError:
            return False

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

            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
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

    # Ollama configuration
    with st.expander("🔧 Ollama Configuration", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            custom_url = st.text_input("Custom Ollama URL", placeholder="http://localhost:11434")
        with col2:
            use_custom = st.checkbox("Use custom URL")

        if use_custom and custom_url:
            ollama_url = custom_url
        else:
            ollama_url = None  # Auto-detect

    # Initialize Ollama client
    ollama = OllamaClient(ollama_url)

    # Check available models
    models_response = ollama.list_models()
    if "error" in models_response:
        st.error(f"Cannot connect to Ollama at {ollama.base_url}: {models_response['error']}")

        st.info("**Setup Instructions:**")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **If running locally:**
            ```bash
            # Install Ollama
            curl -fsSL https://ollama.ai/install.sh | sh

            # Start Ollama service
            ollama serve

            # Pull a model
            ollama pull llama2
            ```
            """)

        with col2:
            st.markdown("""
            **If using Docker:**
            ```bash
            # Start Ollama service
            docker-compose up ollama -d

            # Pull a model
            docker-compose exec ollama ollama pull llama2
            ```
            """)

        st.info("💡 **Tip:** If Ollama is running but on a different URL, use the configuration above to specify a custom URL.")
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
                st.info(f"**Command to run:** `{'docker-compose exec ollama' if ollama.base_url == 'http://ollama:11434' else 'ollama'} ollama pull {new_model}`")
                st.info("This needs to be run in your terminal. The model will be available after pulling.")


if __name__ == "__main__":
    main()