"""Faculty model defining constraints and attributes for academic staff."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from brain.models.exceptions import ValidationError


class Faculty(BaseModel):
    """Represents a faculty member in HanuPlanner.

    Attributes:
        faculty_id: Unique identifier for the faculty.
        name: Name of the faculty member.
        department: Department the faculty member belongs to.
        max_lectures_per_day: Maximum number of lectures they can teach per day.
        preferred_slots: List of slot IDs they prefer.
        unavailable_slots: List of slot IDs they cannot teach in.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    faculty_id: str
    name: str
    department: str
    max_lectures_per_day: int
    preferred_slots: list[str] = Field(default_factory=list)
    unavailable_slots: list[str] = Field(default_factory=list)

    @field_validator("faculty_id", "name", "department")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "string_field", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("max_lectures_per_day")
    @classmethod
    def validate_max_lectures(cls, v: int) -> int:
        """Validate that max lectures per day is a non-negative integer."""
        if v < 0:
            raise ValidationError(
                "max_lectures_per_day", "Max lectures per day must be non-negative"
            )
        return v

    @field_validator("preferred_slots", "unavailable_slots")
    @classmethod
    def validate_slots(cls, v: list[str]) -> list[str]:
        """Validate that slot lists do not contain empty string elements."""
        for slot in v:
            if not slot.strip():
                raise ValidationError(
                    "slots", "Slot identifier cannot be empty or whitespace only"
                )
        return v
