"""Assignment model defining concrete timetable allocations."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class Assignment(BaseModel):
    """Represents a scheduled lecture or lab assignment in a timetable.

    Attributes:
        assignment_id: Unique identifier for the assignment.
        section_id: Section assigned.
        faculty_id: Faculty assigned.
        subject_code: Subject being taught.
        slot_id: Slot in which the session occurs.
        room_id: Room allocated for the session.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    assignment_id: str
    section_id: str
    faculty_id: str
    subject_code: str
    slot_id: str
    room_id: str

    @field_validator(
        "assignment_id",
        "section_id",
        "faculty_id",
        "subject_code",
        "slot_id",
        "room_id",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that all identifier string fields are not empty.

        Checks that values are not whitespace-only.
        """
        if not v.strip():
            raise ValidationError(
                "identifier", "Field cannot be empty or whitespace only"
            )
        return v
