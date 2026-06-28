"""Factory for constructing TeachingSession objects."""

from brain.models.teaching_requirement import TeachingRequirement
from brain.session.session import SessionType, TeachingSession


class SessionFactory:
    """Factory creating individual TeachingSession items with structured fields."""

    @staticmethod
    def create_session(
        requirement: TeachingRequirement,
        suffix: str,
        session_type: SessionType,
        duration: int,
        priority: int = 1,
        dependencies: list[str] | None = None,
    ) -> TeachingSession:
        """Create a TeachingSession from a TeachingRequirement base.

        Args:
            requirement: Parent TeachingRequirement definition.
            suffix: Suffix to append to the subject_code for the session_id.
            session_type: Theory, Lab, Tutorial, or Practical type.
            duration: Slot duration count.
            priority: Scheduling priority heuristic rank.
            dependencies: Session IDs this session depends on.

        Returns:
            A new TeachingSession instance.
        """
        session_id = f"{requirement.subject_code}_{suffix}"
        dep_list = dependencies or []

        return TeachingSession(
            session_id=session_id,
            requirement_id=requirement.requirement_id,
            session_type=session_type,
            duration=duration,
            faculty_id=requirement.faculty_id,
            section_id=requirement.section_id,
            subject_code=requirement.subject_code,
            fixed=False,
            priority=priority,
            dependencies=dep_list,
        )
