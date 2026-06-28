"""Session generation statistics definitions."""

from pydantic import BaseModel, ConfigDict


class SessionStatistics(BaseModel):
    """Statistics calculated during session generation.

    Attributes:
        total_requirements_processed: Number of parsed TeachingRequirement objects.
        total_sessions_generated: Number of constructed TeachingSession objects.
        theory_sessions_count: Count of generated THEORY sessions.
        lab_sessions_count: Count of generated LAB/PRACTICAL sessions.
        tutorial_sessions_count: Count of generated TUTORIAL sessions.
        total_duration_hours: Sum of durations over all generated sessions.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_requirements_processed: int
    total_sessions_generated: int
    theory_sessions_count: int
    lab_sessions_count: int
    tutorial_sessions_count: int
    total_duration_hours: int
