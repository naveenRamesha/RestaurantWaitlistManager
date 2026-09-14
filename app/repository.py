from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models import RestaurantTable, TableCreate, TableUpdate, WaitlistCreate, WaitlistEntry, WaitlistStatus, WaitlistUpdate


class MockDatabase:
    """A deliberately simple repository that can be replaced by a database-backed one."""

    def __init__(self) -> None:
        self.waitlist: dict[str, WaitlistEntry] = {}
        self.tables: dict[str, RestaurantTable] = {}
        self._reference_number = 1041

    def list_waitlist(self) -> list[WaitlistEntry]:
        return sorted(self.waitlist.values(), key=lambda item: item.joined_at)

    def get_waitlist(self, entry_id: str) -> WaitlistEntry | None:
        return self.waitlist.get(entry_id)

    def create_waitlist(self, payload: WaitlistCreate) -> WaitlistEntry:
        self._reference_number += 1
        active_count = sum(item.status in {WaitlistStatus.WAITING, WaitlistStatus.NOTIFIED, WaitlistStatus.CONFIRMED} for item in self.waitlist.values())
        entry = WaitlistEntry(
            id=str(uuid4()),
            reference=f"WL-{self._reference_number}",
            joined_at=datetime.now(UTC),
            estimated_wait_minutes=active_count * 10,
            status=WaitlistStatus.WAITING,
            **payload.model_dump(),
        )
        self.waitlist[entry.id] = entry
        return entry

    def update_waitlist(self, entry: WaitlistEntry, payload: WaitlistUpdate) -> WaitlistEntry:
        data = entry.model_dump()
        data.update(payload.model_dump(exclude_unset=True))
        updated = WaitlistEntry(**data)
        self.waitlist[entry.id] = updated
        return updated

    def save_waitlist(self, entry: WaitlistEntry) -> WaitlistEntry:
        self.waitlist[entry.id] = entry
        return entry

    def list_tables(self) -> list[RestaurantTable]:
        return sorted(self.tables.values(), key=lambda item: item.name)

    def get_table(self, table_id: str) -> RestaurantTable | None:
        return self.tables.get(table_id)

    def create_table(self, payload: TableCreate) -> RestaurantTable:
        table = RestaurantTable(id=str(uuid4()), **payload.model_dump())
        self.tables[table.id] = table
        return table

    def update_table(self, table: RestaurantTable, payload: TableUpdate) -> RestaurantTable:
        data = table.model_dump()
        data.update(payload.model_dump(exclude_unset=True))
        if data["maximum_capacity"] < data["minimum_capacity"]:
            raise ValueError("maximum_capacity must be greater than or equal to minimum_capacity")
        updated = RestaurantTable(**data)
        self.tables[table.id] = updated
        return updated

    def save_table(self, table: RestaurantTable) -> RestaurantTable:
        self.tables[table.id] = table
        return table
