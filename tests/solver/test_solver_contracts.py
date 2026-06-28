"""Tests for HanuPlanner Brain Solver contracts framework."""

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from brain.models.exceptions import ValidationError
from brain.problem.scheduling_instance import SchedulingInstance
from brain.solver import (
    BaseSolver,
    SolverFactory,
    SolverRegistry,
    SolverResult,
    SolverStatus,
)


class MockSolver(BaseSolver):
    """Concrete mock solver implementation for testing interfaces."""

    def __init__(self, val: int = 42) -> None:
        """Initialize MockSolver."""
        self.val = val
        self._stats: dict[str, Any] = {"solve_count": 0}

    def solve(self, instance: SchedulingInstance) -> SolverResult:
        """Execute solve logic."""
        self._stats["solve_count"] += 1
        return SolverResult(
            status=SolverStatus.FEASIBLE,
            scheduled_assignments=(),
            statistics={"count": 1},
            diagnostics={"info": "success"},
            runtime=0.015,
            objective_value=100,
        )

    def supports(self, instance: SchedulingInstance) -> bool:
        """Check supports."""
        return True

    def metadata(self) -> dict[str, Any]:
        """Get metadata."""
        return {"name": "MockSolver", "version": "1.0"}

    def statistics(self) -> dict[str, Any]:
        """Get statistics."""
        return self._stats


@pytest.fixture(autouse=True)
def clean_registry() -> None:
    """Clear registry state before and after each test case."""
    SolverRegistry.clear()


def test_solver_result_valid() -> None:
    """Test valid construction of SolverResult."""
    result = SolverResult(
        status=SolverStatus.OPTIMAL,
        scheduled_assignments=(),
        statistics={"nodes": 10},
        diagnostics={"log": "finished"},
        runtime=0.5,
        objective_value=12.5,
    )
    assert result.status == SolverStatus.OPTIMAL
    assert result.runtime == 0.5
    assert result.objective_value == 12.5


def test_solver_result_negative_runtime() -> None:
    """Test that negative runtime throws validation error."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        SolverResult(
            status=SolverStatus.OPTIMAL,
            runtime=-0.1,
        )


def test_solver_result_defaults() -> None:
    """Test default container values in SolverResult."""
    result = SolverResult(
        status=SolverStatus.UNKNOWN,
        runtime=0.0,
    )
    assert len(result.scheduled_assignments) == 0
    assert len(result.statistics) == 0
    assert len(result.diagnostics) == 0
    assert result.objective_value is None


def test_registry_register_and_get() -> None:
    """Test registering and retrieving solver classes."""
    SolverRegistry.register("Mock", MockSolver)
    solver_cls = SolverRegistry.get_solver_class("Mock")
    assert solver_cls is MockSolver


def test_registry_duplicate_register() -> None:
    """Test duplicate solver names raise ValidationError."""
    SolverRegistry.register("Mock", MockSolver)
    with pytest.raises(ValidationError) as exc:
        SolverRegistry.register("Mock", MockSolver)
    assert "is already registered" in str(exc.value)


def test_registry_empty_name() -> None:
    """Test registering with an empty name key raises ValidationError."""
    with pytest.raises(ValidationError) as exc:
        SolverRegistry.register("  ", MockSolver)
    assert "Registry name key cannot be empty" in str(exc.value)


def test_registry_get_unregistered() -> None:
    """Test looking up unregistered keys raises ValidationError."""
    with pytest.raises(ValidationError) as exc:
        SolverRegistry.get_solver_class("UnknownSolver")
    assert "is not registered" in str(exc.value)


def test_registry_list_solvers() -> None:
    """Test listing all registered keys."""
    SolverRegistry.register("M1", MockSolver)
    SolverRegistry.register("M2", MockSolver)
    assert sorted(SolverRegistry.list_solvers()) == ["M1", "M2"]


def test_registry_clear() -> None:
    """Test clearing all registry mappings."""
    SolverRegistry.register("M1", MockSolver)
    SolverRegistry.clear()
    assert len(SolverRegistry.list_solvers()) == 0


def test_factory_create_solver() -> None:
    """Test factory instantiates concrete registered solvers."""
    SolverRegistry.register("Mock", MockSolver)
    solver = SolverFactory.create_solver("Mock", val=100)
    assert isinstance(solver, MockSolver)
    assert solver.val == 100


def test_factory_create_unregistered() -> None:
    """Test factory raises ValidationError for unregistered names."""
    with pytest.raises(ValidationError) as exc:
        SolverFactory.create_solver("UnknownSolver")
    assert "is not registered" in str(exc.value)


def test_base_solver_abc() -> None:
    """Test abstract base class cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseSolver()  # type: ignore[abstract]


def test_solver_result_immutability() -> None:
    """Test that modifying SolverResult attributes is forbidden."""
    result = SolverResult(
        status=SolverStatus.FEASIBLE,
        runtime=0.1,
    )
    with pytest.raises(PydanticValidationError):
        result.status = SolverStatus.OPTIMAL  # type: ignore[misc]


def test_solver_result_extra_forbid() -> None:
    """Test extra attributes are forbidden in SolverResult."""
    with pytest.raises(PydanticValidationError):
        SolverResult(
            status=SolverStatus.FEASIBLE,
            runtime=0.1,
            extra_field="forbidden",  # type: ignore[call-arg]
        )


def test_solver_status_values() -> None:
    """Verify all StrEnum SolverStatus options match specifications."""
    assert SolverStatus.OPTIMAL == "OPTIMAL"
    assert SolverStatus.FEASIBLE == "FEASIBLE"
    assert SolverStatus.INFEASIBLE == "INFEASIBLE"
    assert SolverStatus.TIMEOUT == "TIMEOUT"
    assert SolverStatus.ABORTED == "ABORTED"
    assert SolverStatus.UNKNOWN == "UNKNOWN"


def test_mock_solver_execution() -> None:
    """Test executing concrete mock solver logic."""
    inst = SchedulingInstance()
    solver = MockSolver()
    result = solver.solve(inst)
    assert result.status == SolverStatus.FEASIBLE
    assert result.runtime == 0.015


def test_mock_solver_supports_true() -> None:
    """Test supports query check on mock solver."""
    inst = SchedulingInstance()
    solver = MockSolver()
    assert solver.supports(inst) is True


def test_mock_solver_metadata() -> None:
    """Test metadata query values."""
    solver = MockSolver()
    meta = solver.metadata()
    assert meta["name"] == "MockSolver"
    assert meta["version"] == "1.0"


def test_mock_solver_statistics() -> None:
    """Test statistics tracking after solver runs."""
    inst = SchedulingInstance()
    solver = MockSolver()
    assert solver.statistics()["solve_count"] == 0
    solver.solve(inst)
    assert solver.statistics()["solve_count"] == 1


def test_mock_solver_runtime_tracking() -> None:
    """Test runtime returns correct solve output result value."""
    inst = SchedulingInstance()
    solver = MockSolver()
    result = solver.solve(inst)
    assert result.runtime == 0.015


def test_mock_solver_objective_value() -> None:
    """Test objective value retrieval from mock solver results."""
    inst = SchedulingInstance()
    solver = MockSolver()
    result = solver.solve(inst)
    assert result.objective_value == 100


def test_mock_solver_diagnostics() -> None:
    """Test diagnostics content in SolverResult output."""
    inst = SchedulingInstance()
    solver = MockSolver()
    result = solver.solve(inst)
    assert result.diagnostics["info"] == "success"


def test_mock_solver_scheduled_assignments() -> None:
    """Test scheduled assignments tuple list in SolverResult."""
    inst = SchedulingInstance()
    solver = MockSolver()
    result = solver.solve(inst)
    assert len(result.scheduled_assignments) == 0


def test_registry_register_strips_whitespace() -> None:
    """Test that solver name keys trim trailing/leading whitespace on registration."""
    SolverRegistry.register("  MockSolverKey  ", MockSolver)
    assert "MockSolverKey" in SolverRegistry.list_solvers()


def test_registry_get_strips_whitespace() -> None:
    """Test that lookups trim whitespace in key names."""
    SolverRegistry.register("MockSolverKey", MockSolver)
    solver_cls = SolverRegistry.get_solver_class("  MockSolverKey  ")
    assert solver_cls is MockSolver


def test_mock_solver_missing_one_abstract_method() -> None:
    """Test subclassing BaseSolver missing an abstract method throws TypeError."""

    class IncompleteSolver(BaseSolver):
        def solve(self, instance: SchedulingInstance) -> SolverResult:
            return SolverResult(status=SolverStatus.UNKNOWN, runtime=0.0)

        def supports(self, instance: SchedulingInstance) -> bool:
            return True

        def metadata(self) -> dict[str, Any]:
            return {}

        # statistics() is missing

    with pytest.raises(TypeError):
        IncompleteSolver()  # type: ignore[abstract]
