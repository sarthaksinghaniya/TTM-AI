"""Builder to construct and initialize ConstraintSets."""

from brain.constraints.constraint_set import ConstraintSet
from brain.constraints.factory import ConstraintFactory
from brain.constraints.hard.credit_completion import CreditCompletionConstraint

# Import all evaluators to register them
from brain.constraints.hard.faculty_overlap import FacultyOverlapConstraint
from brain.constraints.hard.holiday import HolidayConstraint
from brain.constraints.hard.room_overlap import RoomOverlapConstraint
from brain.constraints.registry import ConstraintRegistry
from brain.constraints.soft.balanced_workload import BalancedWorkloadConstraint
from brain.constraints.soft.building_preference import BuildingPreferenceConstraint
from brain.constraints.soft.minimum_gap import MinimumGapConstraint
from brain.constraints.soft.morning_preference import MorningPreferenceConstraint
from brain.models.constraint import Constraint

# Register constraints
ConstraintRegistry.register("Faculty Overlap", FacultyOverlapConstraint)
ConstraintRegistry.register("Room Overlap", RoomOverlapConstraint)
ConstraintRegistry.register("Holiday Overlap", HolidayConstraint)
ConstraintRegistry.register("Credit Completion", CreditCompletionConstraint)
ConstraintRegistry.register("Morning Preference", MorningPreferenceConstraint)
ConstraintRegistry.register("Minimum Gap", MinimumGapConstraint)
ConstraintRegistry.register("Balanced Workload", BalancedWorkloadConstraint)
ConstraintRegistry.register("Building Preference", BuildingPreferenceConstraint)


class ConstraintBuilder:
    """Builder to construct constraint sets from definitions."""

    @staticmethod
    def build(definitions: list[Constraint]) -> ConstraintSet:
        """Build a ConstraintSet from a list of Constraint definitions.

        Args:
            definitions: A list of Constraint definitions.

        Returns:
            A ConstraintSet.
        """
        evaluators = []
        for definition in definitions:
            evaluators.append(ConstraintFactory.build(definition))
        return ConstraintSet(evaluators)
