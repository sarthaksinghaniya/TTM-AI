"""Constraint set representing a collection of active constraints."""

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.score import ScheduleScore
from brain.models.timetable import Timetable


class ConstraintSet:
    """Manages a collection of constraint evaluators and scores timetables."""

    def __init__(self, evaluators: list[BaseConstraintEvaluator]) -> None:
        """Initialize the ConstraintSet.

        Args:
            evaluators: A list of instantiated constraint evaluators.
        """
        self.evaluators = evaluators

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate the timetable against all active constraints.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A combined list of Conflicts.
        """
        conflicts: list[Conflict] = []
        for evaluator in self.evaluators:
            conflicts.extend(evaluator.evaluate(timetable, context))
        return conflicts

    def score(self, timetable: Timetable, context: ConstraintContext) -> ScheduleScore:
        """Calculate the ScheduleScore of the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A ScheduleScore instance.
        """
        hard_violations = 0
        soft_penalty = 0.0

        for evaluator in self.evaluators:
            conflicts = evaluator.evaluate(timetable, context)
            if evaluator.definition.severity == Severity.HARD:
                hard_violations += len(conflicts)
            else:
                soft_penalty += len(conflicts) * evaluator.definition.weight

        soft_score = -soft_penalty
        overall_score = soft_score - (hard_violations * 1000.0)

        return ScheduleScore(
            hard_violations=hard_violations,
            soft_score=soft_score,
            overall_score=overall_score,
        )

    def normalize_weights(self) -> None:
        """Normalize the weights of all soft constraints so that they sum to 1.0.

        If there are no soft constraints or their sum is 0, does nothing.
        """
        soft_evaluators = [
            e for e in self.evaluators if e.definition.severity == Severity.SOFT
        ]
        total_weight = sum(e.definition.weight for e in soft_evaluators)
        if total_weight > 0.0:
            for e in soft_evaluators:
                from brain.models.constraint import Constraint

                new_def = Constraint(
                    constraint_id=e.definition.constraint_id,
                    name=e.definition.name,
                    severity=e.definition.severity,
                    weight=e.definition.weight / total_weight,
                )
                e.definition = new_def
        # Wait, if we mutated it, does type checker / frozen complain?
        # definition is a field on BaseConstraintEvaluator, which is not frozen.
        # But Constraint itself is frozen, which is why we created new_def.
        # So setting e.definition = new_def is perfectly fine and valid python!
