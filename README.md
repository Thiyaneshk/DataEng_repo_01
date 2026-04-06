# de_template

Phase 0 template for:
- Streamlit + uv
- DuckDB first, later Postgres
- CLI (scripts/refresh_data.py) + UI (app/main.py)
- dbt skeleton (dbt/)
- Airflow skeleton (airflow/)

## Learning checkpoints

1. Set up environment:
   - `uv sync`

2. Run the CLI:
   - `uv run python -m scripts.refresh_data`

3. Run the UI:
   - `uv run streamlit run app/main.py`

4. Add Google OAuth in `app/auth.py`.

5. Add Postgres support in `app/db/connection.py`.

6. Initialize dbt inside `dbt/` and point it at DuckDB/Postgres.

7. Add an Airflow DAG in `airflow/dags/` that calls your ETL logic.

---

## Docker Deployment (Phase 1)

### Build Docker Image

```bash
docker build -t stock-ml:latest .
```

### Run Container Locally

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Run container with DuckDB data volume mounted
docker run -d \
  --name stock-ml \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  stock-ml:latest
```

Then open http://localhost:8501 in your browser.

### Common Docker Commands

```bash
# View container logs
docker logs stock-ml

# Follow logs in real-time
docker logs -f stock-ml

# Check container status
docker ps

# Stop container
docker stop stock-ml

# Start container (after stopping)
docker start stock-ml

# Remove container (stops and deletes)
docker rm -f stock-ml

# View container stats
docker stats stock-ml

# Execute command in running container
docker exec -it stock-ml bash
```

### Environment Variables

See `.env.example` for all available configuration options. To use custom environment variables:

```bash
# Copy example to actual .env
cp .env.example .env

# Run container with env file
docker run -d \
  --name stock-ml \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  stock-ml:latest
```

### Data Persistence

- Container mounts `./data` (host) to `/app/data` (container)
- DuckDB database (`app.duckdb`) persists between container restarts
- Data survives `docker stop` but will be deleted with `docker rm -f` unless volume is backed up

### Port Mapping

- Container runs on port `8501` internally
- Exposed to host via `http://localhost:8501`
- To change host port: `-p 9000:8501` maps container 8501 to host 9000

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Container exits immediately | Run `docker logs stock-ml` to see errors |
| App not accessible | Check `docker ps` to verify container is running |
| Port 8501 already in use | Use different port: `-p 9000:8501` |
| DuckDB data lost after restart | Verify `-v $(pwd)/data:/app/data` in docker run command |
| App won't start in container | Ensure all required system dependencies are installed (build-essential in Dockerfile) |

### File Layout (Inside Container)

```
/app
  ├── app/               # Streamlit app code
  ├── data/              # DuckDB database (mounted volume)
  ├── config/            # Configuration files
  ├── dbt/               # dbt project
  ├── scripts/           # CLI scripts
  └── Dockerfile         # Build configuration
```

---

## Docker Compose + Postgres + Airflow (Phase 2)

### Start all services

```bash
# Ensure .env exists and contains required values
cp .env.example .env

# Start all services
docker-compose up -d --build
```

### Verify services

```bash
docker-compose ps
# Streamlit -> http://localhost:8501
# Airflow Web UI -> http://localhost:8080 (admin/admin)
# Postgres -> localhost:5432
```

### Postgres DB client access

- Postgres is exposed to the host on `localhost:5432`
- Connect with any client: DBeaver, TablePlus, pgAdmin, DataGrip, `psql`, etc.
- Default connection string:
  `postgresql://postgres:postgres@localhost:5432/airflow`

### Airflow DAG

- `airflow/dags/etl_prices_dag.py` now coordinates:
  - `load_prices()` into DuckDB
  - `dbt run --target postgres` into Postgres (via `dbt/profiles.yml`)

### Stop services

```bash
docker-compose down
```

### Notes

- In Phase 2, app reads Postgres when `POSTGRES_URL` is set; still falls back to DuckDB.
- `dbt` profile includes both `duckdb` and `postgres` (use `dbt run --target postgres`).

