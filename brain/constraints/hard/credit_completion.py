"""Credit completion hard constraint check."""

from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class CreditCompletionConstraint(BaseConstraintEvaluator):
    """Checks if scheduled subject hours match required credits."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate if subjects are scheduled for their required credits/hours.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []

        # Find required hours for each subject
        subject_hours = {
            s.subject_code: s.theory_hours + s.lab_hours + s.tutorial_hours
            for s in context.subjects
        }

        # Count scheduled hours per section and subject
        scheduled_counts: dict[tuple[str, str], int] = defaultdict(int)
        for assignment in timetable.assignments:
            key = (assignment.section_id, assignment.subject_code)
            scheduled_counts[key] += 1

        # We check all section-subject pairs that are assigned in the timetable
        section_subjects: dict[str, set[str]] = defaultdict(set)
        for assignment in timetable.assignments:
            section_subjects[assignment.section_id].add(assignment.subject_code)

        for section_id, subjects in section_subjects.items():
            for subject_code in subjects:
                req = subject_hours.get(subject_code, 0)
                sched = scheduled_counts[(section_id, subject_code)]
                if sched != req:
                    desc = (
                        f"Section '{section_id}' has {sched} hours scheduled for "
                        f"subject '{subject_code}', but {req} hours are required."
                    )
                    conflicts.append(
                        Conflict(
                            conflict_id=f"CREDIT_MISMATCH_{section_id}_{subject_code}",
                            description=desc,
                            severity=Severity.HARD,
                            suggestion=(
                                f"Adjust assignments so section '{section_id}' has "
                                f"exactly {req} hours for subject '{subject_code}'."
                            ),
                        )
                    )
        return conflicts
