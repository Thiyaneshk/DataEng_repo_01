# 🚀 FastAPI Scaffold

This directory contains the groundwork for a REST API layer.

## Why use an API?
1. **Decoupling**: Your Streamlit app, Mobile app, or Trading Bot can all use the same data source.
2. **Standardization**: Logic for fetching data is centralized.
3. **Integration**: LLMs can use these endpoints as "Tools" to fetch real-time market data.

## Setup & Run
To run the API locally:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Then visit:
- **Interactive Docs**: http://localhost:8000/docs
- **JSON Root**: http://localhost:8000/

## Dependencies
You will need to add `fastapi` and `uvicorn` to your `pyproject.toml` when you are ready to build this out:

```bash
uv add fastapi uvicorn
```
