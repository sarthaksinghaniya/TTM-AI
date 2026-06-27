"""Subject model defining academic subjects/courses."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class Subject(BaseModel):
    """Represents a subject or course in the HanuPlanner engine.

    Attributes:
        subject_code: Unique code for the subject.
        subject_name: Descriptive name of the subject.
        credits: Credit points associated with the course.
        theory_hours: Weekly theory class hours.
        lab_hours: Weekly practical or laboratory class hours.
        tutorial_hours: Weekly tutorial class hours.
        continuous_lab: Indicates if lab sessions must run consecutively.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_code: str
    subject_name: str
    credits: int
    theory_hours: int
    lab_hours: int
    tutorial_hours: int
    continuous_lab: bool

    @field_validator("subject_code", "subject_name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "string_field", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("credits", "theory_hours", "lab_hours", "tutorial_hours")
    @classmethod
    def validate_non_negative_values(cls, v: int) -> int:
        """Validate that credit and hourly values are non-negative."""
        if v < 0:
            raise ValidationError("numerical_field", "Value must be non-negative")
        return v
