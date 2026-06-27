"""Registry for HanuPlanner Brain constraints."""

from typing import ClassVar

from brain.constraints.base import BaseConstraintEvaluator


class ConstraintRegistry:
    """Registry to keep track of available constraint check classes."""

    _registry: ClassVar[dict[str, type[BaseConstraintEvaluator]]] = {}

    @classmethod
    def register(cls, name: str, evaluator_cls: type[BaseConstraintEvaluator]) -> None:
        """Register a new constraint evaluator class.

        Args:
            name: The name of the constraint rule.
            evaluator_cls: The evaluator class to register.
        """
        cls._registry[name] = evaluator_cls

    @classmethod
    def get(cls, name: str) -> type[BaseConstraintEvaluator]:
        """Retrieve a constraint evaluator class by name.

        Args:
            name: The name of the constraint rule.

        Returns:
            The evaluator class.

        Raises:
            KeyError: If the constraint name is not registered.
        """
        if name not in cls._registry:
            raise KeyError(f"Constraint '{name}' is not registered.")
        return cls._registry[name]

    @classmethod
    def list_constraints(cls) -> list[str]:
        """List all registered constraint names.

        Returns:
            A list of registered constraint names.
        """
        return list(cls._registry.keys())
