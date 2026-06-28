"""Base abstract class defining unified timetabling solver interfaces."""

from abc import ABC, abstractmethod
from typing import Any

from brain.problem.scheduling_instance import SchedulingInstance
from brain.solver.solver_result import SolverResult


class BaseSolver(ABC):
    """Abstract Base Class for all schedulers and solvers."""

    @abstractmethod
    def solve(self, instance: SchedulingInstance) -> SolverResult:
        """Execute the scheduling solver on the given problem instance.

        Args:
            instance: Input SchedulingInstance.

        Returns:
            A SolverResult with final status and scheduled assignments.
        """
        pass

    @abstractmethod
    def supports(self, instance: SchedulingInstance) -> bool:
        """Determine if this solver is capable of processing the given instance.

        Args:
            instance: Input SchedulingInstance.

        Returns:
            True if this solver supports the instance parameters, False otherwise.
        """
        pass

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Retrieve solver metadata configurations.

        Returns:
            Key-value dictionary describing the solver details.
        """
        pass

    @abstractmethod
    def statistics(self) -> dict[str, Any]:
        """Retrieve real-time run statistics from the last solve execution.

        Returns:
            Key-value metrics telemetry of the execution run.
        """
        pass
