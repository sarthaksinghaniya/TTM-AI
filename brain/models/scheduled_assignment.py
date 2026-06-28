"""ScheduledAssignment model defining finalized timetable schedules."""

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.assignment import Assignment
from brain.models.exceptions import ValidationError
from brain.models.slot import Day


class ScheduledAssignment(BaseModel):
    """Represents a finalized scheduled session/lecture in a timetable.

    Attributes:
        session_id: Unique identifier for the scheduled assignment session.
        day: Scheduled day of the week.
        slot_id: Slot in which the session occurs.
        room_id: Room allocated for the session.
        duration: Duration of the scheduled session in slots/hours.
        faculty_id: Faculty member assigned.
        section_id: Section assigned.
        subject_code: Subject code being taught.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    day: Day
    slot_id: str
    room_id: str
    duration: int
    faculty_id: str
    section_id: str
    subject_code: str

    @field_validator(
        "session_id",
        "slot_id",
        "room_id",
        "faculty_id",
        "section_id",
        "subject_code",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that all string fields are not empty or whitespace only.

        Args:
            v: Input string.

        Returns:
            The validated string.

        Raises:
            ValidationError: If string is empty or whitespace only.
        """
        if not v.strip():
            raise ValidationError(
                "identifier", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("duration")
    @classmethod
    def validate_positive_duration(cls, v: int) -> int:
        """Validate that the session duration is positive.

        Args:
            v: Input duration value.

        Returns:
            The validated integer.

        Raises:
            ValidationError: If duration is less than 1.
        """
        if v < 1:
            raise ValidationError("duration", "Duration must be at least 1")
        return v

    @classmethod
    def from_assignment(
        cls, assignment: Assignment, day: Day, duration: int
    ) -> Self:
        """Migrate from the older Assignment model format.

        Args:
            assignment: The original Assignment instance.
            day: The Day to map the assignment to.
            duration: The duration of the session.

        Returns:
            A new ScheduledAssignment instance.
        """
        return cls(
            session_id=assignment.assignment_id,
            day=day,
            slot_id=assignment.slot_id,
            room_id=assignment.room_id,
            duration=duration,
            faculty_id=assignment.faculty_id,
            section_id=assignment.section_id,
            subject_code=assignment.subject_code,
        )

    def to_assignment(self) -> Assignment:
        """Convert back to the older Assignment model for backward compatibility.

        Returns:
            An Assignment instance.
        """
        return Assignment(
            assignment_id=self.session_id,
            section_id=self.section_id,
            faculty_id=self.faculty_id,
            subject_code=self.subject_code,
            slot_id=self.slot_id,
            room_id=self.room_id,
        )
