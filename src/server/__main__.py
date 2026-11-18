"""Application entry point for the Door Hardware Verification API."""
from http.server import ThreadingHTTPServer

from .api import Handler
from .database import DB_PATH, initialize


if __name__ == "__main__":
    initialize()
    print(f"Door hardware API ready at http://127.0.0.1:8000 · SQLite: {DB_PATH}")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
