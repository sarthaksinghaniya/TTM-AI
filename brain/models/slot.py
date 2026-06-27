"""Slot model defining individual schedule time slots."""

import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from brain.models.exceptions import ValidationError


class Day(StrEnum):
    """Days of the week used for scheduling."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class Slot(BaseModel):
    """Represents a time slot in the schedule.

    Attributes:
        slot_id: Unique identifier for the slot.
        day: Day of the week.
        start_time: Start time of the slot.
        end_time: End time of the slot.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_id: str
    day: Day
    start_time: datetime.time
    end_time: datetime.time

    @field_validator("slot_id")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that slot_id is not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "slot_id", "Slot ID cannot be empty or whitespace only"
            )
        return v

    @model_validator(mode="after")
    def validate_time_range(self) -> "Slot":
        """Validate that the end time is strictly after the start time."""
        if self.end_time <= self.start_time:
            raise ValidationError("time_range", "End time must be after start time")
        return self
