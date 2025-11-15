#!/usr/bin/env python3
"""
Launcher for the RPi Sensor Node FastAPI service.
"""

import sys
from pathlib import Path

# --- ensure src/ is importable ---
ROOT = Path(__file__).resolve().parents[1]       # project root
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))                     # <— add to import path
# ---------------------------------

import argparse
import uvicorn, logging
from sensor_node.main import create_app, setup_logging
from sensor_node.config import Settings

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Run the RPi Sensor Node API server")
    parser.add_argument("--host", default=None, help="Host to bind (default from .env or 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind (default from .env or 8000)")
    args = parser.parse_args()

    # Load settings from .env (falls back to defaults)
    settings = Settings()

    host = args.host or settings.api_host or "0.0.0.0"
    port = args.port or settings.api_port or 8000

    logging.info(f"Starting FastAPI server on {host}:{port} ...")

    # Launch the FastAPI app defined in sensor_node/main.py
    uvicorn.run(
        "sensor_node.main:create_app",   # use the factory function
        factory=True,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
