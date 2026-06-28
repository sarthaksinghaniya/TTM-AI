"""Builder Pattern for constructing SchedulingInstance objects."""

from typing import Any, Self

from brain.models.faculty import Faculty
from brain.models.room import Room
from brain.models.section import Section
from brain.models.slot import Slot
from brain.models.subject import Subject
from brain.models.teaching_requirement import TeachingRequirement
from brain.problem.instance_validator import InstanceValidator
from brain.problem.scheduling_instance import SchedulingInstance
from brain.session.session import TeachingSession


class SchedulingInstanceBuilder:
    """Fluent Builder for creating a fully validated SchedulingInstance."""

    def __init__(self) -> None:
        """Initialize the builder with empty lists and config dicts."""
        self._faculties: list[Faculty] = []
        self._subjects: list[Subject] = []
        self._rooms: list[Room] = []
        self._sections: list[Section] = []
        self._slots: list[Slot] = []
        self._holidays: list[str] = []
        self._requirements: list[TeachingRequirement] = []
        self._sessions: list[TeachingSession] = []
        self._config: dict[str, str | int | float | bool] = {}
        self._metadata: dict[str, str | int | float | bool] = {}
        self._constraint_set: Any = None

    def set_faculties(self, faculties: list[Faculty]) -> Self:
        """Set the list of faculties.

        Args:
            faculties: List of Faculty members.

        Returns:
            The builder instance.
        """
        self._faculties = faculties
        return self

    def set_subjects(self, subjects: list[Subject]) -> Self:
        """Set the list of subjects.

        Args:
            subjects: List of Subject course codes.

        Returns:
            The builder instance.
        """
        self._subjects = subjects
        return self

    def set_rooms(self, rooms: list[Room]) -> Self:
        """Set the list of rooms.

        Args:
            rooms: List of Rooms.

        Returns:
            The builder instance.
        """
        self._rooms = rooms
        return self

    def set_sections(self, sections: list[Section]) -> Self:
        """Set the list of sections.

        Args:
            sections: List of student Sections.

        Returns:
            The builder instance.
        """
        self._sections = sections
        return self

    def set_slots(self, slots: list[Slot]) -> Self:
        """Set the list of slots.

        Args:
            slots: List of calendar Slots.

        Returns:
            The builder instance.
        """
        self._slots = slots
        return self

    def set_holidays(self, holidays: list[str]) -> Self:
        """Set the list of holidays.

        Args:
            holidays: List of holiday slot IDs.

        Returns:
            The builder instance.
        """
        self._holidays = holidays
        return self

    def set_requirements(self, requirements: list[TeachingRequirement]) -> Self:
        """Set the list of teaching requirements.

        Args:
            requirements: List of TeachingRequirement curriculum requests.

        Returns:
            The builder instance.
        """
        self._requirements = requirements
        return self

    def set_sessions(self, sessions: list[TeachingSession]) -> Self:
        """Set the list of sessions.

        Args:
            sessions: List of TeachingSession tasks.

        Returns:
            The builder instance.
        """
        self._sessions = sessions
        return self

    def set_config(self, config: dict[str, str | int | float | bool]) -> Self:
        """Set configuration flags.

        Args:
            config: Config key-value map.

        Returns:
            The builder instance.
        """
        self._config = config
        return self

    def set_metadata(self, metadata: dict[str, str | int | float | bool]) -> Self:
        """Set metadata parameters.

        Args:
            metadata: Metadata key-value map.

        Returns:
            The builder instance.
        """
        self._metadata = metadata
        return self

    def set_constraint_set(self, constraint_set: Any) -> Self:
        """Set constraint set class.

        Args:
            constraint_set: Constraint evaluation engine.

        Returns:
            The builder instance.
        """
        self._constraint_set = constraint_set
        return self

    def build(self) -> SchedulingInstance:
        """Construct, validate, and return the SchedulingInstance.

        Returns:
            A fully validated SchedulingInstance.

        Raises:
            ValidationError: If cross-reference validation fails.
        """
        instance = SchedulingInstance(
            faculties=tuple(self._faculties),
            subjects=tuple(self._subjects),
            rooms=tuple(self._rooms),
            sections=tuple(self._sections),
            slots=tuple(self._slots),
            holidays=tuple(self._holidays),
            requirements=tuple(self._requirements),
            sessions=tuple(self._sessions),
            config=self._config,
            metadata=self._metadata,
            constraint_set=self._constraint_set,
        )
        validator = InstanceValidator()
        validator.validate(instance)
        return instance
