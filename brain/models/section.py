"""Section model defining student cohort sections."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class Section(BaseModel):
    """Represents a cohort of students (a section) to be scheduled.

    Attributes:
        section_id: Unique identifier for the section.
        program: Academic program/department of the section.
        year: Year of study.
        strength: Number of students in this section.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    section_id: str
    program: str
    year: int
    strength: int

    @field_validator("section_id", "program")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that section_id and program are not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "string_field", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        """Validate that year is a positive integer."""
        if v <= 0:
            raise ValidationError("year", "Year must be positive")
        return v

    @field_validator("strength")
    @classmethod
    def validate_strength(cls, v: int) -> int:
        """Validate that strength is a positive integer."""
        if v <= 0:
            raise ValidationError("strength", "Section strength must be positive")
        return v
