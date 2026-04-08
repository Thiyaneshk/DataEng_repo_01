# Local RAG Architecture

> Guide for local LLM (Ollama) integration on Mac mini M4.

1. **Extraction**: dbt mart `fct_equity_features_1d` generates structured context (RSI, EMA, returns).
2. **Knowledge Base**:
   - **Structured Data**: SQL queries against Postgres/DuckDB.
   - **Unstructured Data**: Analyst reports, news RSS feeds, or company filings saved as PDF/Text.
3. **Indexing**:
   - Use **LlamaIndex** to create a unified index over both SQL and Documents.
   - Use **Ollama (Llama 3)** or **OpenAI** for generating embeddings.
4. **Retrieval**:
   - **Semantic Search**: Using a Vector DB (like `pgvector` in Postgres or `ChromaDB`).
   - **Structured Retrieval**: Using Text-to-SQL to query market metrics.
5. **Generation**: Ollama for local reasoning or OpenAI for high-reasoning tasks.

### 🛠️ Tech Stack Requirements for RAG

#### Local Path (Privacy & Cost)
- **Engine**: Ollama (running `llama3` or `mistral`).
- **Framework**: LlamaIndex (easier for beginners to connect SQL + Docs).
- **Vector DB**: `pgvector` (extension for your existing Postgres).
- **Compute**: Mac mini M4 is excellent for this!

#### Cloud Path (Performance)
- **Engine**: OpenAI GPT-4o.
- **Framework**: LangChain (for building complex "agents").
- **Vector DB**: Pinecone or MongoDB Atlas Vector Search.

### 🧠 How to Learn This
1. **Step 1**: Write a Python script that takes a user question (e.g., "Is AAPL bullish?") and converts it into a SQL query.
2. **Step 2**: Use **LlamaIndex** "QueryEngine" to automate that process.
3. **Step 3**: Add "Memory" to your chat so the AI remembers your previous questions about the TSX or Nifty 50.

### Staff DE Pro Tip:
Ollama on M4 leverages Metal acceleration. For optimal performance, allocate at least 8GB of memory to Docker if you run the stack in containers. When using RAG, the "Quality of Retrieval" is more important than the "Size of the LLM."
