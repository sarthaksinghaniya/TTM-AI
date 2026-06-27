"""Subject validator implementing duplicate check and credits consistency check."""

import logging

from brain.models.subject import Subject
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning

logger = logging.getLogger(__name__)


class SubjectValidator(BaseValidator[list[Subject]]):
    """Validator for subject records.

    Checks for duplicate subject codes and credit/hour consistency.
    """

    def validate(self, data: list[Subject]) -> ValidationResult:
        """Validate a list of subjects.

        Checks:
            - duplicate subject codes
            - credits mismatch

        Args:
            data: List of Subject instances.

        Returns:
            A ValidationResult.
        """
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        seen_codes: set[str] = set()
        for subject in data:
            # Check duplicate subject codes
            if subject.subject_code in seen_codes:
                msg = f"Duplicate subject code found: '{subject.subject_code}'"
                logger.error(msg)
                errors.append(msg)
            seen_codes.add(subject.subject_code)

            # Check credits mismatch
            # Rule: credits must equal theory_hours + tutorial_hours + (lab_hours // 2)
            expected_credits = (
                subject.theory_hours + subject.tutorial_hours + (subject.lab_hours // 2)
            )
            if subject.credits != expected_credits:
                msg = (
                    f"Credits mismatch for subject '{subject.subject_code}': "
                    f"credits={subject.credits}, expected={expected_credits} "
                    f"(theory: {subject.theory_hours}, "
                    f"tutorial: {subject.tutorial_hours}, "
                    f"lab: {subject.lab_hours})"
                )
                logger.error(msg)
                errors.append(msg)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
