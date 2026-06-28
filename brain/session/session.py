"""Atomic TeachingSession model definitions."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class SessionType(StrEnum):
    """Supported session types for course schedules."""

    THEORY = "Theory"
    LAB = "Lab"
    TUTORIAL = "Tutorial"
    PRACTICAL = "Practical"


class TeachingSession(BaseModel):
    """Represents an atomic, unscheduled lecture or lab session.

    Attributes:
        session_id: Unique identifier for the session (e.g. DBMS_T1).
        requirement_id: Reference to the parent TeachingRequirement.
        session_type: The class session format (e.g. THEORY, LAB).
        duration: Slot duration (positive integer representing slot count/hours).
        faculty_id: Target faculty member identifier.
        section_id: Target student section identifier.
        subject_code: Target course subject code.
        fixed: Whether the session has a pre-allocated locked slot.
        priority: Priority ranking for scheduling heuristic selection.
        dependencies: List of session IDs this session depends on.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    requirement_id: str
    session_type: SessionType
    duration: int
    faculty_id: str
    section_id: str
    subject_code: str
    fixed: bool = False
    priority: int = 1
    dependencies: list[str] = []

    @field_validator(
        "session_id",
        "requirement_id",
        "faculty_id",
        "section_id",
        "subject_code",
    )
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that target string fields are not empty or whitespace only.

        Args:
            v: Input string value.

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

    @field_validator("priority")
    @classmethod
    def validate_positive_priority(cls, v: int) -> int:
        """Validate that the priority is positive.

        Args:
            v: Input priority value.

        Returns:
            The validated integer.

        Raises:
            ValidationError: If priority is less than 1.
        """
        if v < 1:
            raise ValidationError("priority", "Priority must be at least 1")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: list[str]) -> list[str]:
        """Validate dependency items.

        Args:
            v: Input list of references.

        Returns:
            The validated list.

        Raises:
            ValidationError: If any dependency string is empty or whitespace only.
        """
        for item in v:
            if not item.strip():
                raise ValidationError(
                    "dependency",
                    "Dependency string cannot be empty or whitespace only",
                )
        return v
