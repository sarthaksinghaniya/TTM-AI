"""Curriculum model defining course syllabus planning requirements."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError
from brain.models.teaching_requirement import TeachingRequirement


class Curriculum(BaseModel):
    """Represents a curriculum planning dataset holding multiple teaching requirements.

    Attributes:
        curriculum_id: Unique identifier for the curriculum planning set.
        name: Name of the curriculum.
        requirements: List of associated TeachingRequirement planning entities.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    curriculum_id: str
    name: str
    requirements: list[TeachingRequirement]

    @field_validator("curriculum_id", "name")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that target string fields are not empty or whitespace only.

        Args:
            v: Input string value.

        Returns:
            The validated string.

        Raises:
            ValidationError: If string is empty or whitespace only.
        """
        if not v.strip():
            raise ValidationError(
                "identifier", "Field cannot be empty or whitespace only"
            )
        return v

    @field_validator("requirements")
    @classmethod
    def validate_unique_requirements(
        cls, v: list[TeachingRequirement]
    ) -> list[TeachingRequirement]:
        """Ensure all requirement_ids within a Curriculum are unique.

        Args:
            v: List of TeachingRequirement planning entities.

        Returns:
            The validated list.

        Raises:
            ValidationError: If duplicate requirement IDs exist in the curriculum.
        """
        seen = set()
        for req in v:
            if req.requirement_id in seen:
                raise ValidationError(
                    "requirements",
                    f"Duplicate requirement ID '{req.requirement_id}' "
                    "found in curriculum",
                )
            seen.add(req.requirement_id)
        return v
