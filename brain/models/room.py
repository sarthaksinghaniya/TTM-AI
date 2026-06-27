"""Room model defining classroom and laboratory resources."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class RoomType(StrEnum):
    """Types of rooms available for scheduling."""

    THEORY = "THEORY"
    LAB = "LAB"
    TUTORIAL = "TUTORIAL"
    SEMINAR = "SEMINAR"


class Room(BaseModel):
    """Represents a room in the university.

    Attributes:
        room_id: Unique identifier for the room.
        capacity: Seating/student capacity of the room.
        room_type: Purpose of the room (e.g., THEORY, LAB).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    room_id: str
    capacity: int
    room_type: RoomType

    @field_validator("room_id")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that room_id is not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "room_id", "Room ID cannot be empty or whitespace only"
            )
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: int) -> int:
        """Validate that the capacity is greater than zero."""
        if v <= 0:
            raise ValidationError("capacity", "Room capacity must be greater than zero")
        return v
