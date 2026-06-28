"""TeachingRequirement model defining curriculum planning requirements."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class TeachingRequirement(BaseModel):
    """Represents a curriculum planning teaching requirement constraint.

    Attributes:
        requirement_id: Unique identifier for the teaching requirement.
        faculty_id: Target faculty member identifier.
        section_id: Target section identifier.
        subject_code: Target subject code.
        weekly_theory_hours: Planned weekly theory hours.
        weekly_lab_hours: Planned weekly lab hours.
        preferred_room_type: Required room type (e.g. THEORY, LAB).
        batch: Target batch name/identifier (e.g. Batch A).
        constraint_refs: List of identifiers referencing applicable constraints.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: str
    faculty_id: str
    section_id: str
    subject_code: str
    weekly_theory_hours: int
    weekly_lab_hours: int
    preferred_room_type: str
    batch: str
    constraint_refs: list[str]

    @field_validator(
        "requirement_id",
        "faculty_id",
        "section_id",
        "subject_code",
        "preferred_room_type",
        "batch",
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

    @field_validator("weekly_theory_hours", "weekly_lab_hours")
    @classmethod
    def validate_non_negative_hours(cls, v: int) -> int:
        """Validate that hours are non-negative.

        Args:
            v: Input hours count.

        Returns:
            The validated integer.

        Raises:
            ValidationError: If hours value is negative.
        """
        if v < 0:
            raise ValidationError("hours", "Hours cannot be negative")
        return v

    @field_validator("constraint_refs")
    @classmethod
    def validate_constraint_refs(cls, v: list[str]) -> list[str]:
        """Validate constraint reference items.

        Args:
            v: Input list of references.

        Returns:
            The validated list.

        Raises:
            ValidationError: If any reference string is empty or whitespace only.
        """
        for ref in v:
            if not ref.strip():
                raise ValidationError(
                    "constraint_ref",
                    "Constraint reference cannot be empty or whitespace only",
                )
        return v
