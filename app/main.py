from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.models import (
    AssistantRequest,
    AuthResponse,
    LoginRequest,
    RestaurantTable,
    Role,
    SeatRequest,
    TableCreate,
    TableStatus,
    TableUpdate,
    User,
    WaitlistCreate,
    WaitlistEntry,
    WaitlistStatus,
    WaitlistUpdate,
)
from app.repository import MockDatabase


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def error(status_code: int, code: str, message: str) -> ApiError:
    return ApiError(status_code, code, message)


def create_app(*, seed: bool = False) -> FastAPI:
    app = FastAPI(title="Restaurant Waitlist Manager API", version="0.1.0", openapi_url="/openapi.json")
    database = MockDatabase()
    if seed:
        seed_demo_data(database)
    current_user = User(id="user-host-1", name="Sam Adams", email="host@thegardenroom.example", role=Role.HOST, restaurant_id="restaurant-garden-room")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_database() -> MockDatabase:
        return database

    Db = Annotated[MockDatabase, Depends(get_database)]

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first_error = exc.errors()[0]
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": first_error["msg"]}})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/auth/login", response_model=AuthResponse)
    def login(payload: LoginRequest) -> AuthResponse:
        if payload.password != "demo":
            raise error(401, "INVALID_CREDENTIALS", "The supplied email or password is invalid.")
        user = current_user.model_copy(update={"email": payload.email})
        return AuthResponse(access_token="mock-access-token", refresh_token="mock-refresh-token", user=user)

    @app.post("/api/v1/auth/refresh", response_model=AuthResponse)
    def refresh_token() -> AuthResponse:
        return AuthResponse(access_token="mock-access-token-refreshed", refresh_token="mock-refresh-token", user=current_user)

    @app.post("/api/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout() -> Response:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/auth/me", response_model=User)
    def me() -> User:
        return current_user

    @app.get("/api/v1/waitlist", response_model=list[WaitlistEntry])
    def list_waitlist(db: Db) -> list[WaitlistEntry]:
        return db.list_waitlist()

    @app.post("/api/v1/waitlist", response_model=WaitlistEntry, status_code=status.HTTP_201_CREATED)
    def create_waitlist(payload: WaitlistCreate, db: Db) -> WaitlistEntry:
        return db.create_waitlist(payload)

    @app.get("/api/v1/waitlist/{waitlist_id}", response_model=WaitlistEntry)
    def get_waitlist(waitlist_id: str, db: Db) -> WaitlistEntry:
        return require_entry(waitlist_id, db)

    @app.patch("/api/v1/waitlist/{waitlist_id}", response_model=WaitlistEntry)
    def update_waitlist(waitlist_id: str, payload: WaitlistUpdate, db: Db) -> WaitlistEntry:
        return db.update_waitlist(require_entry(waitlist_id, db), payload)

    @app.delete("/api/v1/waitlist/{waitlist_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_waitlist(waitlist_id: str, db: Db) -> Response:
        transition(require_entry(waitlist_id, db), WaitlistStatus.CANCELLED, {WaitlistStatus.WAITING}, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/api/v1/waitlist/{waitlist_id}/notify", response_model=WaitlistEntry)
    def notify(waitlist_id: str, db: Db) -> WaitlistEntry:
        return transition(require_entry(waitlist_id, db), WaitlistStatus.NOTIFIED, {WaitlistStatus.WAITING}, db, notified_at=datetime.now(UTC))

    @app.post("/api/v1/waitlist/{waitlist_id}/confirm", response_model=WaitlistEntry)
    def confirm(waitlist_id: str, db: Db) -> WaitlistEntry:
        return transition(require_entry(waitlist_id, db), WaitlistStatus.CONFIRMED, {WaitlistStatus.NOTIFIED}, db)

    @app.post("/api/v1/waitlist/{waitlist_id}/cancel", response_model=WaitlistEntry)
    def cancel(waitlist_id: str, db: Db) -> WaitlistEntry:
        return transition(require_entry(waitlist_id, db), WaitlistStatus.CANCELLED, {WaitlistStatus.WAITING}, db)

    @app.post("/api/v1/waitlist/{waitlist_id}/seat", response_model=WaitlistEntry)
    def seat(waitlist_id: str, payload: SeatRequest, db: Db) -> WaitlistEntry:
        entry = require_entry(waitlist_id, db)
        if entry.status != WaitlistStatus.CONFIRMED:
            raise error(409, "INVALID_WAITLIST_STATUS", "Customer must confirm before they can be seated.")
        table = require_table(payload.table_id, db)
        if table.status != TableStatus.AVAILABLE:
            raise error(409, "TABLE_NOT_AVAILABLE", "The selected table is not available.")
        if entry.party_size > table.maximum_capacity:
            raise error(409, "TABLE_CAPACITY_MISMATCH", "The selected table cannot seat this party.")
        seated = entry.model_copy(update={"status": WaitlistStatus.SEATED, "table_id": table.id, "seated_at": datetime.now(UTC)})
        db.save_waitlist(seated)
        db.save_table(table.model_copy(update={"status": TableStatus.OCCUPIED}))
        return seated

    @app.get("/api/v1/tables", response_model=list[RestaurantTable])
    def list_tables(db: Db) -> list[RestaurantTable]:
        return db.list_tables()

    @app.post("/api/v1/tables", response_model=RestaurantTable, status_code=status.HTTP_201_CREATED)
    def create_table(payload: TableCreate, db: Db) -> RestaurantTable:
        return db.create_table(payload)

    @app.get("/api/v1/tables/{table_id}", response_model=RestaurantTable)
    def get_table(table_id: str, db: Db) -> RestaurantTable:
        return require_table(table_id, db)

    @app.patch("/api/v1/tables/{table_id}", response_model=RestaurantTable)
    def update_table(table_id: str, payload: TableUpdate, db: Db) -> RestaurantTable:
        try:
            return db.update_table(require_table(table_id, db), payload)
        except ValueError as exc:
            raise error(422, "VALIDATION_ERROR", str(exc)) from exc

    @app.get("/api/v1/reports/waitlist")
    def waitlist_report(db: Db) -> dict[str, int]:
        entries = db.list_waitlist()
        waiting = [item for item in entries if item.status == WaitlistStatus.WAITING]
        return {"waiting_parties": len(waiting), "total_entries": len(entries), "cancelled_parties": sum(item.status == WaitlistStatus.CANCELLED for item in entries)}

    @app.get("/api/v1/reports/tables")
    def table_report(db: Db) -> dict[str, int]:
        tables = db.list_tables()
        return {"total_tables": len(tables), "available_tables": sum(item.status == TableStatus.AVAILABLE for item in tables), "occupied_tables": sum(item.status == TableStatus.OCCUPIED for item in tables)}

    @app.get("/api/v1/reports/operations")
    def operations_report(db: Db) -> dict[str, int]:
        entries = db.list_waitlist()
        active = [item for item in entries if item.status in {WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED, WaitlistStatus.CONFIRMED}]
        average_party_size = round(sum(item.party_size for item in active) / len(active)) if active else 0
        return {"active_waitlist_entries": len(active), "average_party_size": average_party_size, "customers_seated": sum(item.status == WaitlistStatus.SEATED for item in entries)}

    @app.get("/api/v1/ai/wait-estimate/{waitlist_id}")
    def wait_estimate(waitlist_id: str, db: Db) -> dict[str, int | str]:
        entry = require_entry(waitlist_id, db)
        return {"waitlist_id": entry.id, "estimated_wait_minutes": entry.estimated_wait_minutes, "range_start_minutes": max(0, entry.estimated_wait_minutes - 5), "range_end_minutes": entry.estimated_wait_minutes + 5, "confidence": "HIGH"}

    @app.get("/api/v1/ai/table-recommendations")
    def recommendations(db: Db) -> dict[str, list[dict[str, str | int]]]:
        available_tables = [table for table in db.list_tables() if table.status == TableStatus.AVAILABLE]
        waiting = [entry for entry in db.list_waitlist() if entry.status == WaitlistStatus.WAITING]
        matches: list[dict[str, str | int]] = []
        for table in available_tables:
            matching_entries = [entry for entry in waiting if entry.party_size <= table.maximum_capacity]
            if matching_entries:
                entry = matching_entries[0]
                matches.append({"table_id": table.id, "waitlist_id": entry.id, "customer_name": entry.customer_name, "party_size": entry.party_size, "reason": f"{table.name} accommodates this party of {entry.party_size}."})
        return {"recommendations": matches}

    @app.get("/api/v1/ai/insights")
    def insights(db: Db) -> dict[str, str]:
        wait_count = sum(item.status == WaitlistStatus.WAITING for item in db.list_waitlist())
        return {"insight": f"{wait_count} parties are currently waiting.", "recommendation": "Prioritise available tables that fit the longest-waiting party."}

    @app.post("/api/v1/ai/assistant")
    def assistant(payload: AssistantRequest, db: Db) -> dict[str, str]:
        active = sum(item.status in {WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED, WaitlistStatus.CONFIRMED} for item in db.list_waitlist())
        return {"answer": f"There are currently {active} active parties. This deterministic mock assistant received: {payload.question}"}

    return app


def require_entry(entry_id: str, db: MockDatabase) -> WaitlistEntry:
    entry = db.get_waitlist(entry_id)
    if entry is None:
        raise error(404, "WAITLIST_NOT_FOUND", "The requested waitlist entry does not exist.")
    return entry


def require_table(table_id: str, db: MockDatabase) -> RestaurantTable:
    table = db.get_table(table_id)
    if table is None:
        raise error(404, "TABLE_NOT_FOUND", "The requested table does not exist.")
    return table


def transition(entry: WaitlistEntry, target: WaitlistStatus, allowed: set[WaitlistStatus], db: MockDatabase, **updates: object) -> WaitlistEntry:
    if entry.status not in allowed:
        raise error(409, "INVALID_WAITLIST_STATUS", f"Customer cannot transition from {entry.status} to {target}.")
    return db.save_waitlist(entry.model_copy(update={"status": target, **updates}))


def seed_demo_data(db: MockDatabase) -> None:
    """Populate the application-only mock database; test apps start empty."""
    table_specs = [
        ("T1", 1, 2, "Window", TableStatus.OCCUPIED),
        ("T2", 2, 4, "Main Dining", TableStatus.AVAILABLE),
        ("T3", 2, 4, "Main Dining", TableStatus.OCCUPIED),
        ("T4", 2, 4, "Patio", TableStatus.AVAILABLE),
        ("T5", 4, 6, "Main Dining", TableStatus.CLEANING),
        ("T6", 4, 8, "Private Room", TableStatus.OCCUPIED),
    ]
    for name, minimum_capacity, maximum_capacity, location, table_status in table_specs:
        db.create_table(TableCreate(name=name, minimum_capacity=minimum_capacity, maximum_capacity=maximum_capacity, location=location, status=table_status))

    maya = db.create_waitlist(WaitlistCreate(customer_name="Maya Patel", phone_number="(555) 014-2981", party_size=4, seating_preference="INDOOR", special_requirements="High chair"))
    db.create_waitlist(WaitlistCreate(customer_name="James Carter", phone_number="(555) 012-7604", party_size=2, seating_preference="BOOTH"))
    db.create_waitlist(WaitlistCreate(customer_name="Olivia Chen", phone_number="(555) 019-3402", party_size=3, seating_preference="OUTDOOR"))
    noah = db.create_waitlist(WaitlistCreate(customer_name="Noah Williams", phone_number="(555) 017-1986", party_size=2, seating_preference="WINDOW"))
    amelia = db.create_waitlist(WaitlistCreate(customer_name="Amelia Rivera", phone_number="(555) 010-5241", party_size=4))
    db.save_waitlist(maya.model_copy(update={"estimated_wait_minutes": 8}))
    db.save_waitlist(noah.model_copy(update={"status": WaitlistStatus.NOTIFIED, "notified_at": datetime.now(UTC)}))
    db.save_waitlist(amelia.model_copy(update={"status": WaitlistStatus.CONFIRMED, "notified_at": datetime.now(UTC)}))


app = create_app(seed=True)
