"""Registry for registering and looking up BaseSolver implementations."""

from typing import ClassVar

from brain.models.exceptions import ValidationError
from brain.solver.base_solver import BaseSolver


class SolverRegistry:
    """Class-level registry for mapping solver identifiers to their classes."""

    _registry: ClassVar[dict[str, type[BaseSolver]]] = {}

    @classmethod
    def register(cls, name: str, solver_cls: type[BaseSolver]) -> None:
        """Register a solver class under a unique name key.

        Args:
            name: Solver identifier name (e.g. 'Greedy').
            solver_cls: Solver class implementation.

        Raises:
            ValidationError: If key is already registered or empty.
        """
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValidationError(
                "solver_registry", "Registry name key cannot be empty"
            )

        if cleaned_name in cls._registry:
            raise ValidationError(
                "solver_registry", f"Solver '{cleaned_name}' is already registered."
            )

        cls._registry[cleaned_name] = solver_cls

    @classmethod
    def get_solver_class(cls, name: str) -> type[BaseSolver]:
        """Look up and retrieve a registered solver class.

        Args:
            name: Solver identifier name key.

        Returns:
            The solver class.

        Raises:
            ValidationError: If the solver key is not registered.
        """
        cleaned_name = name.strip()
        if cleaned_name not in cls._registry:
            raise ValidationError(
                "solver_registry", f"Solver '{cleaned_name}' is not registered."
            )
        return cls._registry[cleaned_name]

    @classmethod
    def list_solvers(cls) -> list[str]:
        """List all currently registered solver keys.

        Returns:
            List of string identifier names.
        """
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered solver classes."""
        cls._registry.clear()
