"""Section validator implementing section strength vs room capacity checks."""

import logging

from brain.models.assignment import Assignment
from brain.models.room import Room
from brain.models.section import Section
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning

logger = logging.getLogger(__name__)


class SectionValidator(BaseValidator[list[Assignment]]):
    """Validator for student sections against assignment details.

    Checks if section strengths exceed allocated room capacities.
    """

    def __init__(self, sections: list[Section], rooms: list[Room]) -> None:
        """Initialize the validator.

        Args:
            sections: List of all sections.
            rooms: List of all rooms.
        """
        self.section_strengths = {s.section_id: s.strength for s in sections}
        self.room_capacities = {r.room_id: r.capacity for r in rooms}

    def validate(self, data: list[Assignment]) -> ValidationResult:
        """Validate assignments for section strength capacity compatibility.

        Checks:
            - strength > capacity

        Args:
            data: List of Assignment instances.

        Returns:
            A ValidationResult.
        """
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        for assignment in data:
            strength = self.section_strengths.get(assignment.section_id)
            capacity = self.room_capacities.get(assignment.room_id)

            if strength is not None and capacity is not None:
                if strength > capacity:
                    msg = (
                        f"Strength exceeds capacity: "
                        f"assignment '{assignment.assignment_id}' "
                        f"assigns section '{assignment.section_id}' "
                        f"(strength {strength}) to room '{assignment.room_id}' "
                        f"(capacity {capacity})"
                    )
                    logger.error(msg)
                    errors.append(msg)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
