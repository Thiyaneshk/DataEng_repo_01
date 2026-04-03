from dataclasses import dataclass, field
import os
import tomllib
from pathlib import Path
from typing import Dict, Any, List

@dataclass
class AppConfig:
    app_name: str = os.getenv("APP_NAME", "Equity Data Platform")
    project_root: Path = Path(__file__).parent.parent
    duckdb_path: Path = Path(os.getenv("DUCKDB_PATH", "data/app.duckdb"))
    symbols_config_path: Path = project_root / "config" / "symbols.toml"
    symbols_data: Dict[str, Any] = field(default_factory=dict)
    postgres_url: str | None = os.getenv("POSTGRES_URL")

    def __post_init__(self):
        if self.symbols_config_path.exists():
            with open(self.symbols_config_path, "rb") as f:
                self.symbols_data = tomllib.load(f)
        else:
            self.symbols_data = {"symbols": {"AAPL": {}}, "settings": {"default_period": "5d", "default_interval": "5m"}}

    @property
    def symbols_list(self) -> List[str]:
        config_syms = list(self.symbols_data.get("symbols", {}).keys())
        try:
            from app.db.utils import get_watchlist_symbols
            watchlist_syms = get_watchlist_symbols()
        except (ImportError, Exception):
            watchlist_syms = []
        return list(set(config_syms + watchlist_syms))

    @property
    def default_period(self) -> str:
        return self.symbols_data.get("settings", {}).get("default_period", "5d")

def get_config() -> AppConfig:
    return AppConfig()
