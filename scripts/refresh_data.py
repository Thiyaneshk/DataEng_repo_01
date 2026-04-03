from app.core.etl.prices import load_prices_5m
if __name__ == "__main__":
    load_prices_5m(period="5d")
