# Local RAG Architecture

> Guide for local LLM (Ollama) integration on Mac mini M4.

1. **Extraction**: dbt mart `fct_equity_features_1d` generates context.
2. **Indexing**: Use LlamaIndex + Ollama for embeddings.
3. **Retrieval**: Vector search on DuckDB features.
4. **Generation**: Ollama (Llama 3) for local reasoning.

### Staff DE Pro Tip:
Ollama on M4 leverages Metal acceleration. For optimal performance, allocate at least 8GB of memory to Docker if you run the stack in containers.
