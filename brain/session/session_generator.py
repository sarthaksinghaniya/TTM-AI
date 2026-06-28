"""Session generator breaking requirements down into atomic sessions."""

from brain.models.exceptions import ValidationError
from brain.models.teaching_requirement import TeachingRequirement
from brain.session.session import SessionType, TeachingSession
from brain.session.session_factory import SessionFactory
from brain.session.session_statistics import SessionStatistics


class SessionGenerator:
    """Generates atomic, unscheduled TeachingSession objects from requirements."""

    def generate_sessions(
        self,
        requirements: list[TeachingRequirement],
        max_theory_duration: int = 1,
        link_lab_to_theory: bool = False,
    ) -> tuple[list[TeachingSession], SessionStatistics]:
        """Convert list of teaching requirements into atomic schedulable sessions.

        Args:
            requirements: List of TeachingRequirement resource demands.
            max_theory_duration: Maximum duration for individual theory sessions.
            link_lab_to_theory: If True, link lab sessions to the first theory session.

        Returns:
            Tuple of (list of generated TeachingSession, SessionStatistics).

        Raises:
            ValidationError: If max_theory_duration is less than 1.
        """
        if max_theory_duration < 1:
            raise ValidationError(
                "max_theory_duration",
                "Max theory duration must be at least 1",
            )

        sessions: list[TeachingSession] = []
        theory_count = 0
        lab_count = 0
        tut_count = 0
        total_duration = 0

        for req in requirements:
            # Determine if this requirement represents a tutorial session
            is_tutorial = (
                req.preferred_room_type.upper() == "TUTORIAL"
                or "tutorial" in [c.lower() for c in req.constraint_refs]
            )

            # 1. Generate Theory / Tutorial sessions
            theory_hours = req.weekly_theory_hours
            theory_session_ids = []
            if theory_hours > 0:
                remaining = theory_hours
                theory_splits = []
                while remaining > 0:
                    alloc = min(remaining, max_theory_duration)
                    theory_splits.append(alloc)
                    remaining -= alloc

                for idx, dur in enumerate(theory_splits, 1):
                    suffix = f"T{idx}"
                    s_type = SessionType.TUTORIAL if is_tutorial else SessionType.THEORY

                    session = SessionFactory.create_session(
                        requirement=req,
                        suffix=suffix,
                        session_type=s_type,
                        duration=dur,
                        priority=1,
                    )
                    sessions.append(session)
                    theory_session_ids.append(session.session_id)
                    total_duration += dur

                    if is_tutorial:
                        tut_count += 1
                    else:
                        theory_count += 1

            # 2. Generate Lab sessions
            lab_hours = req.weekly_lab_hours
            if lab_hours > 0:
                suffix = "L1"
                deps = []
                if link_lab_to_theory and theory_hours > 0 and theory_session_ids:
                    deps = [theory_session_ids[0]]

                session = SessionFactory.create_session(
                    requirement=req,
                    suffix=suffix,
                    session_type=SessionType.LAB,
                    duration=lab_hours,
                    priority=1,
                    dependencies=deps,
                )
                sessions.append(session)
                lab_count += 1
                total_duration += lab_hours

        stats = SessionStatistics(
            total_requirements_processed=len(requirements),
            total_sessions_generated=len(sessions),
            theory_sessions_count=theory_count,
            lab_sessions_count=lab_count,
            tutorial_sessions_count=tut_count,
            total_duration_hours=total_duration,
        )

        return sessions, stats
