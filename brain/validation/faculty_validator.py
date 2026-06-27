"""Faculty validator implementing duplicate check and week availability check."""

import logging

from brain.models.faculty import Faculty
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning

logger = logging.getLogger(__name__)


class FacultyValidator(BaseValidator[list[Faculty]]):
    """Validator for faculty records.

    Checks for duplicate IDs and full-week unavailability.
    """

    def __init__(self, all_slots: list[str] | None = None) -> None:
        """Initialize the validator.

        Args:
            all_slots: List of all active slot IDs in the schedule calendar.
        """
        self.all_slots = all_slots or []

    def validate(self, data: list[Faculty]) -> ValidationResult:
        """Validate a list of faculty records.

        Checks:
            - duplicate faculty ids
            - faculty unavailable full week

        Args:
            data: List of Faculty instances.

        Returns:
            A ValidationResult.
        """
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        seen_ids: set[str] = set()
        for faculty in data:
            # Check duplicate faculty ids
            if faculty.faculty_id in seen_ids:
                msg = f"Duplicate faculty ID found: '{faculty.faculty_id}'"
                logger.error(msg)
                errors.append(msg)
            seen_ids.add(faculty.faculty_id)

            # Check faculty unavailable full week
            if self.all_slots:
                is_unavailable_all_week = set(self.all_slots).issubset(
                    set(faculty.unavailable_slots)
                )
                if is_unavailable_all_week:
                    msg = f"Faculty unavailable all week: {faculty.faculty_id}"
                    logger.error(msg)
                    errors.append(msg)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
