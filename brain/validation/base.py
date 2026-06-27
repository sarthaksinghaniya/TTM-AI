"""Base classes and interfaces for validation in HanuPlanner Brain."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from brain.models.exceptions import ValidationError


class ValidationWarning(BaseModel):
    """Represents a non-critical validation warning.

    Attributes:
        code: A short warning identifier code.
        message: Detailed warning description.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str


class ValidationResult(BaseModel):
    """Holds the overall outcome of a validation run.

    Attributes:
        is_valid: True if no validation errors occurred.
        errors: List of error messages.
        warnings: List of validation warnings.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[ValidationWarning] = Field(default_factory=list)


class BaseValidator[T](ABC):
    """Abstract base class for all validators in the scheduling engine."""

    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """Validate a single instance or dataset of type T.

        Args:
            data: The data object or collection to validate.

        Returns:
            A ValidationResult.
        """
        pass

    def validate_many(self, items: list[T]) -> ValidationResult:
        """Validate a list of objects of type T.

        Args:
            items: A list of objects to validate.

        Returns:
            A combined ValidationResult.
        """
        combined_errors: list[str] = []
        combined_warnings: list[ValidationWarning] = []

        for item in items:
            res = self.validate(item)
            combined_errors.extend(res.errors)
            combined_warnings.extend(res.warnings)

        return ValidationResult(
            is_valid=len(combined_errors) == 0,
            errors=combined_errors,
            warnings=combined_warnings,
        )

    async def validate_async(self, data: T) -> ValidationResult:
        """Asynchronously validate a single instance or dataset of type T.

        Args:
            data: The data object or collection to validate.

        Returns:
            A ValidationResult.
        """
        import asyncio

        return await asyncio.to_thread(self.validate, data)

    def validate_enforce(self, data: T) -> None:
        """Validate the data and raise a ValidationError if invalid.

        Args:
            data: The data object or collection to validate.

        Raises:
            ValidationError: If validation fails.
        """
        res = self.validate(data)
        if not res.is_valid:
            raise ValidationError(res.errors[0])
