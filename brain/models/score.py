"""Score model representing timetable quality metrics."""

from pydantic import BaseModel, ConfigDict, field_validator

from brain.models.exceptions import ValidationError


class ScheduleScore(BaseModel):
    """Represents the multi-criteria score of a scheduled timetable.

    Attributes:
        hard_violations: Number of hard constraint violations (must be 0).
        soft_score: Combined soft constraint score (higher/less-negative is better).
        overall_score: Overall calculated metric combining hard and soft scores.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    hard_violations: int
    soft_score: float
    overall_score: float

    @field_validator("hard_violations")
    @classmethod
    def validate_hard_violations(cls, v: int) -> int:
        """Validate that hard violations are non-negative."""
        if v < 0:
            raise ValidationError(
                "hard_violations", "Hard violations must be non-negative"
            )
        return v

    def normalized_score(self) -> float:
        """Compute the normalized quality score between 0.0 and 1.0.

        If there is any hard violation, normalized score is 0.0.
        Otherwise, soft score is mapped to range [0.0, 1.0]
        using 1 / (1 + |soft_score|).

        Returns:
            A float value in the range [0.0, 1.0].
        """
        if self.hard_violations > 0:
            return 0.0
        return 1.0 / (1.0 + abs(self.soft_score))

    def grade(self) -> str:
        """Return a letter grade representation of the timetable score.

        Returns:
            Grade letter from F (worst) to A+ (best).
        """
        if self.hard_violations > 0:
            return "F"
        norm = self.normalized_score()
        if norm >= 0.95:
            return "A+"
        if norm >= 0.85:
            return "A"
        if norm >= 0.70:
            return "B"
        if norm >= 0.50:
            return "C"
        return "D"
