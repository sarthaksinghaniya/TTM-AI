"""Calendar validator implementing holiday overlap checks."""

import logging

from brain.models.assignment import Assignment
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning

logger = logging.getLogger(__name__)


class CalendarValidator(BaseValidator[list[Assignment]]):
    """Validator for timetable slots against the calendar constraints.

    Checks for scheduling overlaps with holidays.
    """

    def __init__(self, holidays: list[str] | None = None) -> None:
        """Initialize the validator.

        Args:
            holidays: List of slot IDs representing holidays/unavailable slots.
        """
        self.holidays = set(holidays or [])

    def validate(self, data: list[Assignment]) -> ValidationResult:
        """Validate assignments against calendar constraints.

        Checks:
            - holiday overlap

        Args:
            data: List of Assignment instances.

        Returns:
            A ValidationResult.
        """
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        for assignment in data:
            if assignment.slot_id in self.holidays:
                msg = (
                    f"Holiday overlap: assignment '{assignment.assignment_id}' "
                    f"is scheduled on holiday slot '{assignment.slot_id}'"
                )
                logger.error(msg)
                errors.append(msg)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
