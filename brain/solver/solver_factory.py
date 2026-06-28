"""Factory for instantiating registered BaseSolver implementations."""

from typing import Any

from brain.solver.base_solver import BaseSolver
from brain.solver.solver_registry import SolverRegistry


class SolverFactory:
    """Factory retrieving registered solver classes and building instances."""

    @staticmethod
    def create_solver(name: str, **kwargs: Any) -> BaseSolver:
        """Create and instantiate a registered solver by name key.

        Args:
            name: Registered name key of the solver class.
            kwargs: Constructor keyword arguments.

        Returns:
            An instantiated concrete BaseSolver object.

        Raises:
            ValidationError: If the solver key is not registered.
        """
        solver_cls = SolverRegistry.get_solver_class(name)
        return solver_cls(**kwargs)
