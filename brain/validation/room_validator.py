"""Room validator implementing duplicate check and capacity boundary checks."""

import logging

from brain.models.room import Room
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning

logger = logging.getLogger(__name__)


class RoomValidator(BaseValidator[list[Room]]):
    """Validator for room records.

    Checks for duplicate IDs and negative/zero capacity.
    """

    def validate(self, data: list[Room]) -> ValidationResult:
        """Validate a list of rooms.

        Checks:
            - duplicate room ids
            - negative room capacity

        Args:
            data: List of Room instances.

        Returns:
            A ValidationResult.
        """
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        seen_ids: set[str] = set()
        for room in data:
            # Check duplicate room ids
            if room.room_id in seen_ids:
                msg = f"Duplicate room ID found: '{room.room_id}'"
                logger.error(msg)
                errors.append(msg)
            seen_ids.add(room.room_id)

            # Check negative or zero capacity
            if room.capacity <= 0:
                msg = (
                    f"Room '{room.room_id}' capacity must be positive: "
                    f"got {room.capacity}"
                )
                logger.error(msg)
                errors.append(msg)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
