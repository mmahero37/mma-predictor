#!/usr/bin/env bash
# Start the FastAPI app with uvicorn.
exec uvicorn mma_app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
