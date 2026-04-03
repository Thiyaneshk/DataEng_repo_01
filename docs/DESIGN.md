# DESIGN DOCUMENT

## 1. System Architecture
Source (yfinance) -> Raw (DuckDB raw_prices_5m) -> Staging -> Marts (Indicators) -> UI (Streamlit)

## 2. RAG & AI
- Context extracted from `fct_equity_features_1d`.
- Ollama for local LLM execution.
- LlamaIndex for vector retrieval.
