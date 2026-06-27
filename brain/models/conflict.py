"""Conflict model representing scheduling clashes or violations."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.constraint import Severity
from brain.models.exceptions import ValidationError


class Conflict(BaseModel):
    """Represents a scheduled constraint violation or resource conflict.

    Attributes:
        conflict_id: Unique identifier for the conflict.
        description: Message detailing the nature of the conflict.
        severity: HARD or SOFT violation.
        suggestion: Advice/remedy for resolving this conflict.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    conflict_id: str
    description: str
    severity: Severity
    suggestion: str

    @field_validator("conflict_id", "description", "suggestion")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that conflict fields are not empty or whitespace only."""
        if not v.strip():
            raise ValidationError(
                "string_field", "Field cannot be empty or whitespace only"
            )
        return v
