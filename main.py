"""Entry point — starts the FastAPI server via uvicorn."""

import uvicorn
from backend.api import app  # noqa: F401

if __name__ == "__main__":
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
