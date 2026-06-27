"""Constraint model defining scheduling rules and penalties."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class Severity(StrEnum):
    """Severity levels for constraints."""

    HARD = "HARD"
    SOFT = "SOFT"


class Constraint(BaseModel):
    """Represents a rule used to evaluate timetable quality.

    Attributes:
        constraint_id: Unique identifier for the constraint.
        name: Name of the constraint rule.
        severity: HARD (must satisfy) or SOFT (preferred).
        weight: Importance weight associated with satisfying this constraint.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_id: str
    name: str
    severity: Severity
    weight: float

    @field_validator("constraint_id", "name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that identifier and name fields are not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "string_field", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Validate that the weight is non-negative."""
        if v < 0.0:
            raise ValidationError("weight", "Constraint weight must be non-negative")
        return v
