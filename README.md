# Seatly
Restaurant Waitlist Manager is a web-based application that helps restaurants manage customers waiting for tables.

The application allows restaurant staff to:

Add customers to a waitlist.
Record party size and seating preferences.
Track estimated waiting time.
Monitor table availability.
Seat customers when a suitable table becomes available.
Notify customers when their table is ready.
Track waitlist history and statistics.
Manage multiple restaurants or locations.
Use AI to improve wait-time estimation, customer prioritisation, and operational insights.

The application should be designed using Spec-Driven Development (SDD) principles, where this specification acts as the source of truth for requirements, behaviour, APIs, data models, and acceptance criteria.

## Backend

The FastAPI service follows the repository's [OpenAPI contract](openapi.yaml) and currently persists data in memory.

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at `/docs`.

Run the backend tests with:

```powershell
uv run pytest
```
