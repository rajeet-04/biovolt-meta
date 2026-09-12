# Backend

Planned owner: FastAPI service.

Responsibilities beginning in Phase 1:

- device WebSocket gateway
- dashboard WebSocket gateway
- server timestamps
- scientific derived metrics
- experiment lifecycle
- calibration profiles
- SQLite persistence
- CSV export

Phase 0 contains no backend runtime code.

## Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest -v
ruff check .
ruff format --check .
uvicorn biovolt_backend.main:app --reload --app-dir src
```
