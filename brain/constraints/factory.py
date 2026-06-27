"""Factory for instantiating HanuPlanner Brain constraints."""

from brain.constraints.base import BaseConstraintEvaluator
from brain.constraints.registry import ConstraintRegistry
from brain.models.constraint import Constraint


class ConstraintFactory:
    """Factory class to build constraint evaluator instances."""

    @staticmethod
    def build(definition: Constraint) -> BaseConstraintEvaluator:
        """Build a constraint evaluator from a Constraint definition.

        Args:
            definition: The Constraint model containing weight, severity, etc.

        Returns:
            An instance of BaseConstraintEvaluator.
        """
        evaluator_cls = ConstraintRegistry.get(definition.name)
        return evaluator_cls(definition)
