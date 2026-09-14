from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Role(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    HOST = "HOST"


class SeatingPreference(str, Enum):
    ANY = "ANY"
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    BAR = "BAR"
    BOOTH = "BOOTH"
    WINDOW = "WINDOW"


class WaitlistStatus(str, Enum):
    WAITING = "WAITING"
    NOTIFIED = "NOTIFIED"
    CONFIRMED = "CONFIRMED"
    SEATED = "SEATED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    EXPIRED = "EXPIRED"


class TableStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    CLEANING = "CLEANING"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class User(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    restaurant_id: str


class LoginRequest(BaseModel):
    email: str
    password: Annotated[str, Field(min_length=1)]


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User


class WaitlistCreate(BaseModel):
    customer_name: Annotated[str, Field(min_length=1)]
    phone_number: Annotated[str, Field(min_length=1)]
    email: str | None = None
    party_size: Annotated[int, Field(ge=1)]
    seating_preference: SeatingPreference = SeatingPreference.ANY
    special_requirements: str | None = None
    notes: str | None = None


class WaitlistUpdate(BaseModel):
    customer_name: Annotated[str, Field(min_length=1)] | None = None
    phone_number: Annotated[str, Field(min_length=1)] | None = None
    email: str | None = None
    party_size: Annotated[int, Field(ge=1)] | None = None
    seating_preference: SeatingPreference | None = None
    special_requirements: str | None = None
    notes: str | None = None


class WaitlistEntry(WaitlistCreate):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    reference: str
    joined_at: datetime
    estimated_wait_minutes: int
    status: WaitlistStatus
    notified_at: datetime | None = None
    seated_at: datetime | None = None
    table_id: str | None = None


class TableCreate(BaseModel):
    name: Annotated[str, Field(min_length=1)]
    minimum_capacity: Annotated[int, Field(ge=1)]
    maximum_capacity: Annotated[int, Field(ge=1)]
    location: Annotated[str, Field(min_length=1)]
    status: TableStatus = TableStatus.AVAILABLE

    @model_validator(mode="after")
    def maximum_is_not_smaller_than_minimum(self) -> "TableCreate":
        if self.maximum_capacity < self.minimum_capacity:
            raise ValueError("maximum_capacity must be greater than or equal to minimum_capacity")
        return self


class TableUpdate(BaseModel):
    name: Annotated[str, Field(min_length=1)] | None = None
    minimum_capacity: Annotated[int, Field(ge=1)] | None = None
    maximum_capacity: Annotated[int, Field(ge=1)] | None = None
    location: Annotated[str, Field(min_length=1)] | None = None
    status: TableStatus | None = None


class RestaurantTable(TableCreate):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    active: bool = True


class SeatRequest(BaseModel):
    table_id: str


class AssistantRequest(BaseModel):
    question: Annotated[str, Field(min_length=1)]
