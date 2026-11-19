"""Application entry point for the Door Hardware Verification API."""
from http.server import ThreadingHTTPServer
from threading import Thread

from .api import Handler
from .database import DB_PATH, initialize
from .catalog_refresh import refresh_daily


if __name__ == "__main__":
    initialize()
    Thread(target=refresh_daily, name="catalog-refresh", daemon=True).start()
    print(f"Door hardware API ready at http://127.0.0.1:8000 · SQLite: {DB_PATH}")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
