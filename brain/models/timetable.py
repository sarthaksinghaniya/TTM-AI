"""Timetable model holding assignments and schedules."""

from typing import Self

from pydantic import BaseModel, ConfigDict

from brain.models.assignment import Assignment
from brain.models.exceptions import ValidationError


class Timetable(BaseModel):
    """Holds a set of scheduled course assignments.

    Attributes:
        assignments: List of all scheduled assignments.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    assignments: list[Assignment]

    def get_faculty_schedule(self, faculty_id: str) -> list[Assignment]:
        """Retrieve all assignments associated with a specific faculty member.

        Args:
            faculty_id: Unique identifier for the faculty member.

        Returns:
            List of assignments matching the given faculty_id.
        """
        return [a for a in self.assignments if a.faculty_id == faculty_id]

    def get_room_schedule(self, room_id: str) -> list[Assignment]:
        """Retrieve all assignments associated with a specific room.

        Args:
            room_id: Unique identifier for the room.

        Returns:
            List of assignments matching the given room_id.
        """
        return [a for a in self.assignments if a.room_id == room_id]

    def get_section_schedule(self, section_id: str) -> list[Assignment]:
        """Retrieve all assignments associated with a specific section.

        Args:
            section_id: Unique identifier for the student section.

        Returns:
            List of assignments matching the given section_id.
        """
        return [a for a in self.assignments if a.section_id == section_id]

    def serialize(self) -> str:
        """Serialize the timetable to a JSON string representation.

        Returns:
            JSON serialized string of the timetable.
        """
        return self.model_dump_json()

    @classmethod
    def deserialize(cls, json_str: str) -> Self:
        """Deserialize a JSON string representation into a Timetable instance.

        Args:
            json_str: The JSON string representation of the timetable.

        Returns:
            A new instance of Timetable.

        Raises:
            ValidationError: If the JSON is invalid or fails validation.
        """
        try:
            return cls.model_validate_json(json_str)
        except Exception as err:
            raise ValidationError("Failed to deserialize timetable", str(err)) from err
