"""SchedulingInstance model definitions representing a complete timetabling problem."""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from brain.models.exceptions import ValidationError
from brain.models.faculty import Faculty
from brain.models.room import Room
from brain.models.section import Section
from brain.models.slot import Slot
from brain.models.subject import Subject
from brain.models.teaching_requirement import TeachingRequirement
from brain.session.session import TeachingSession


class SchedulingInstance(BaseModel):
    """Immutable, hashable value object representing a timetabling problem.

    Attributes:
        faculties: Tuple of Faculty members.
        subjects: Tuple of course Subjects.
        rooms: Tuple of Rooms.
        sections: Tuple of student Sections.
        slots: Tuple of Slots.
        holidays: Tuple of slot IDs that are holidays.
        requirements: Tuple of TeachingRequirement curriculum requests.
        sessions: Tuple of TeachingSession atomic tasks to schedule.
        config: Dict of key-value configuration flags.
        metadata: Dict of key-value metadata parameters.
        constraint_set: Optional runtime constraint set (excluded from JSON).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    faculties: tuple[Faculty, ...] = ()
    subjects: tuple[Subject, ...] = ()
    rooms: tuple[Room, ...] = ()
    sections: tuple[Section, ...] = ()
    slots: tuple[Slot, ...] = ()
    holidays: tuple[str, ...] = ()
    requirements: tuple[TeachingRequirement, ...] = ()
    sessions: tuple[TeachingSession, ...] = ()
    config: dict[str, str | int | float | bool] = Field(default_factory=dict)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    constraint_set: Any = Field(default=None, exclude=True)

    def __hash__(self) -> int:
        """Hash the immutable scheduling instance values.

        Returns:
            Computed hash integer.
        """
        return hash(self.to_json())

    def __eq__(self, other: Any) -> bool:
        """Check equality of two SchedulingInstance objects.

        Args:
            other: Other object to compare.

        Returns:
            True if instances are equivalent, False otherwise.
        """
        if not isinstance(other, SchedulingInstance):
            return False
        return (
            self.faculties == other.faculties
            and self.subjects == other.subjects
            and self.rooms == other.rooms
            and self.sections == other.sections
            and self.slots == other.slots
            and self.holidays == other.holidays
            and self.requirements == other.requirements
            and self.sessions == other.sessions
            and self.config == other.config
            and self.metadata == other.metadata
        )

    def clone(self, **updates: Any) -> Self:
        """Create a modified clone of this instance with specified updates.

        Args:
            updates: Attributes to update in the new clone.

        Returns:
            A new SchedulingInstance containing the updates.
        """
        data = self.model_dump()
        if "constraint_set" not in updates:
            updates["constraint_set"] = self.constraint_set

        for field in [
            "faculties",
            "subjects",
            "rooms",
            "sections",
            "slots",
            "holidays",
            "requirements",
            "sessions",
        ]:
            if field in updates:
                updates[field] = tuple(updates[field])
            elif field in data:
                data[field] = tuple(data[field])

        data.update(updates)
        return self.__class__(**data)

    def to_json(self) -> str:
        """Serialize this instance to a JSON string representation.

        Returns:
            JSON serialized string.
        """
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize a JSON string representation into a SchedulingInstance.

        Args:
            json_str: JSON string.

        Returns:
            SchedulingInstance instance.

        Raises:
            ValidationError: If deserialization fails.
        """
        try:
            return cls.model_validate_json(json_str)
        except Exception as err:
            raise ValidationError(
                "instance_serialization", f"Failed to deserialize instance: {err}"
            ) from err

    def statistics(self) -> dict[str, int | float]:
        """Compute statistics of the scheduling instance.

        Returns:
            Dictionary containing statistic metrics.
        """
        total_duration = sum(s.duration for s in self.sessions)
        return {
            "faculties_count": len(self.faculties),
            "subjects_count": len(self.subjects),
            "rooms_count": len(self.rooms),
            "sections_count": len(self.sections),
            "slots_count": len(self.slots),
            "holidays_count": len(self.holidays),
            "requirements_count": len(self.requirements),
            "sessions_count": len(self.sessions),
            "total_demand_duration": total_duration,
        }

    def summary(self) -> str:
        """Get a human-readable multi-line summary of the scheduling instance.

        Returns:
            Summary string.
        """
        stats = self.statistics()
        holiday_info = (
            f"Slots:          {stats['slots_count']} "
            f"(Holidays: {stats['holidays_count']})\n"
        )
        session_info = (
            f"Sessions:       {stats['sessions_count']} "
            f"(Total Duration: {stats['total_demand_duration']} slots)\n"
        )
        return (
            "HanuPlanner Brain Scheduling Instance Summary\n"
            "============================================\n"
            f"Faculties:      {stats['faculties_count']}\n"
            f"Subjects:       {stats['subjects_count']}\n"
            f"Rooms:          {stats['rooms_count']}\n"
            f"Sections:       {stats['sections_count']}\n"
            f"{holiday_info}"
            f"Requirements:   {stats['requirements_count']}\n"
            f"{session_info}"
            "============================================"
        )
