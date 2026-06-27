"""Tests for HanuPlanner Brain constraints engine."""

import datetime
from typing import cast

import pytest

from brain.constraints import (
    ConstraintBuilder,
    ConstraintContext,
    ConstraintFactory,
    ConstraintRegistry,
    ConstraintSet,
)
from brain.constraints.hard.credit_completion import CreditCompletionConstraint
from brain.constraints.hard.faculty_overlap import FacultyOverlapConstraint
from brain.constraints.hard.holiday import HolidayConstraint
from brain.constraints.hard.room_overlap import RoomOverlapConstraint
from brain.constraints.soft.balanced_workload import BalancedWorkloadConstraint
from brain.constraints.soft.building_preference import BuildingPreferenceConstraint
from brain.constraints.soft.minimum_gap import MinimumGapConstraint
from brain.constraints.soft.morning_preference import MorningPreferenceConstraint
from brain.models import (
    Assignment,
    Constraint,
    Day,
    Room,
    RoomType,
    Severity,
    Slot,
    Subject,
    Timetable,
)


def test_registry_operations() -> None:
    """Test registering, retrieving, and listing constraint classes."""
    # Retrieve existing constraint
    cls = ConstraintRegistry.get("Faculty Overlap")
    assert cls == FacultyOverlapConstraint

    # List registered constraints
    registered = ConstraintRegistry.list_constraints()
    assert "Faculty Overlap" in registered
    assert "Room Overlap" in registered

    # Attempt retrieving unregistered constraint raises KeyError
    with pytest.raises(KeyError):
        ConstraintRegistry.get("Nonexistent Constraint")


def test_factory_build() -> None:
    """Test ConstraintFactory building from definition."""
    definition = Constraint(
        constraint_id="C01",
        name="Faculty Overlap",
        severity=Severity.HARD,
        weight=1.0,
    )
    evaluator = ConstraintFactory.build(definition)
    assert isinstance(evaluator, FacultyOverlapConstraint)
    assert evaluator.definition == definition


def test_faculty_overlap_constraint() -> None:
    """Test FacultyOverlapConstraint detects double-booked faculty."""
    definition = Constraint(
        constraint_id="C01",
        name="Faculty Overlap",
        severity=Severity.HARD,
        weight=1.0,
    )
    evaluator = FacultyOverlapConstraint(definition)

    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )

    # No overlap
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S01",
        room_id="R2",
    )
    t_valid = Timetable(assignments=[a1, a2])
    assert len(evaluator.evaluate(t_valid, context)) == 0

    # Overlap (same faculty, same slot)
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S01",
        room_id="R2",
    )
    t_invalid = Timetable(assignments=[a1, a3])
    conflicts = evaluator.evaluate(t_invalid, context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.HARD
    assert "double-booked" in conflicts[0].description


def test_room_overlap_constraint() -> None:
    """Test RoomOverlapConstraint detects double-booked rooms."""
    definition = Constraint(
        constraint_id="C02",
        name="Room Overlap",
        severity=Severity.HARD,
        weight=1.0,
    )
    evaluator = RoomOverlapConstraint(definition)

    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )

    # Overlap (same room, same slot)
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S01",
        room_id="R1",
    )
    t_invalid = Timetable(assignments=[a1, a2])
    conflicts = evaluator.evaluate(t_invalid, context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.HARD
    assert "Room 'R1' is double-booked" in conflicts[0].description


def test_holiday_constraint() -> None:
    """Test HolidayConstraint detects assignments scheduled on holidays."""
    definition = Constraint(
        constraint_id="C03",
        name="Holiday Overlap",
        severity=Severity.HARD,
        weight=1.0,
    )
    evaluator = HolidayConstraint(definition)

    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[], holidays=["S01"]
    )

    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    t = Timetable(assignments=[a1])
    conflicts = evaluator.evaluate(t, context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.HARD
    assert "holiday slot 'S01'" in conflicts[0].description


def test_credit_completion_constraint() -> None:
    """Test CreditCompletionConstraint checks hoursScheduled vs hoursRequired."""
    definition = Constraint(
        constraint_id="C04",
        name="Credit Completion",
        severity=Severity.HARD,
        weight=1.0,
    )
    evaluator = CreditCompletionConstraint(definition)

    sub = Subject(
        subject_code="CS101",
        subject_name="Intro to CS",
        credits=3,
        theory_hours=2,
        lab_hours=1,
        tutorial_hours=0,
        continuous_lab=False,
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[sub], sections=[], slots=[]
    )

    # Valid (exactly 3 hours scheduled)
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S02",
        room_id="R1",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S03",
        room_id="R1",
    )
    t_valid = Timetable(assignments=[a1, a2, a3])
    assert len(evaluator.evaluate(t_valid, context)) == 0

    # Invalid (only 2 hours scheduled)
    t_invalid = Timetable(assignments=[a1, a2])
    conflicts = evaluator.evaluate(t_invalid, context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.HARD
    assert "2 hours scheduled" in conflicts[0].description


def test_morning_preference_constraint() -> None:
    """Test MorningPreferenceConstraint penalizes afternoon scheduling."""
    definition = Constraint(
        constraint_id="C05",
        name="Morning Preference",
        severity=Severity.SOFT,
        weight=2.0,
    )
    evaluator = MorningPreferenceConstraint(definition)

    s_morning = Slot(
        slot_id="S01",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s_afternoon = Slot(
        slot_id="S02",
        day=Day.MONDAY,
        start_time=datetime.time(14, 0),
        end_time=datetime.time(15, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s_morning, s_afternoon]
    )

    # Morning assignment (no conflict)
    a_morning = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    assert len(evaluator.evaluate(Timetable(assignments=[a_morning]), context)) == 0

    # Afternoon assignment (conflict)
    a_afternoon = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S02",
        room_id="R1",
    )
    conflicts = evaluator.evaluate(Timetable(assignments=[a_afternoon]), context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.SOFT
    assert "afternoon" in conflicts[0].description


def test_minimum_gap_constraint() -> None:
    """Test MinimumGapConstraint checks for idle window periods."""
    definition = Constraint(
        constraint_id="C06",
        name="Minimum Gap",
        severity=Severity.SOFT,
        weight=1.5,
    )
    evaluator = MinimumGapConstraint(definition)

    s1 = Slot(
        slot_id="S01",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S02",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    s3 = Slot(
        slot_id="S03",
        day=Day.MONDAY,
        start_time=datetime.time(11, 0),
        end_time=datetime.time(12, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1, s2, s3]
    )

    # Consecutive (no gap)
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S02",
        room_id="R1",
    )
    t_consecutive = Timetable(assignments=[a1, a2])
    assert len(evaluator.evaluate(t_consecutive, context)) == 0

    # Gap (S02 is left idle between S01 and S03)
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S03",
        room_id="R1",
    )
    t_gap = Timetable(assignments=[a1, a3])
    conflicts = evaluator.evaluate(t_gap, context)
    assert len(conflicts) == 1
    assert conflicts[0].severity == Severity.SOFT
    assert "idle gap" in conflicts[0].description


def test_balanced_workload_constraint() -> None:
    """Test BalancedWorkloadConstraint penalizes day workload excesses."""
    definition = Constraint(
        constraint_id="C07",
        name="Balanced Workload",
        severity=Severity.SOFT,
        weight=1.0,
    )
    evaluator = BalancedWorkloadConstraint(definition)

    slots = [
        Slot(
            slot_id=f"S{i}",
            day=Day.MONDAY,
            start_time=datetime.time(i, 0),
            end_time=datetime.time(i + 1, 0),
        )
        for i in range(8, 14)
    ]
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=slots
    )

    # 4 classes on MONDAY (no conflict)
    assigns_valid = [
        Assignment(
            assignment_id=f"A{i}",
            section_id="SEC_A",
            faculty_id="F1",
            subject_code="CS101",
            slot_id=f"S{i}",
            room_id="R1",
        )
        for i in range(8, 12)
    ]
    assert len(evaluator.evaluate(Timetable(assignments=assigns_valid), context)) == 0

    assigns_invalid = [
        *assigns_valid,
        Assignment(
            assignment_id="A12",
            section_id="SEC_A",
            faculty_id="F1",
            subject_code="CS101",
            slot_id="S12",
            room_id="R1",
        ),
    ]
    conflicts = evaluator.evaluate(Timetable(assignments=assigns_invalid), context)
    assert len(conflicts) == 1
    assert "exceeds the balance limit" in conflicts[0].description


def test_building_preference_constraint() -> None:
    """Test BuildingPreferenceConstraint penalizes room transition changes."""
    definition = Constraint(
        constraint_id="C08",
        name="Building Preference",
        severity=Severity.SOFT,
        weight=1.5,
    )
    evaluator = BuildingPreferenceConstraint(definition)

    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    r1 = Room(room_id="LH101", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="LH102", capacity=50, room_type=RoomType.THEORY)
    r3 = Room(room_id="CS201", capacity=50, room_type=RoomType.THEORY)
    r_no_letters = Room(room_id="101", capacity=50, room_type=RoomType.THEORY)
    r_empty = Room.model_construct(room_id="", capacity=50, room_type=RoomType.THEORY)

    context = ConstraintContext(
        faculties=[],
        rooms=[r1, r2, r3, r_no_letters, r_empty],
        subjects=[],
        sections=[],
        slots=[s1, s2],
    )

    # Same building 'LH' (no conflict)
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="LH101",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="LH102",
    )
    assert len(evaluator.evaluate(Timetable(assignments=[a1, a2]), context)) == 0

    # Building transition 'LH' -> 'CS' (conflict)
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="CS201",
    )
    conflicts = evaluator.evaluate(Timetable(assignments=[a1, a3]), context)
    assert len(conflicts) == 1
    assert "change buildings from 'LH' to 'CS'" in conflicts[0].description

    # Numeric room ID fallback check (uses '1' as building name)
    a4 = Assignment(
        assignment_id="A4",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="101",
    )
    conflicts_numeric = evaluator.evaluate(Timetable(assignments=[a1, a4]), context)
    assert len(conflicts_numeric) == 1
    assert "change buildings from 'LH' to '1'" in conflicts_numeric[0].description

    # Empty room ID fallback check (uses '' as building name)
    a5 = Assignment.model_construct(
        assignment_id="A5",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="",
    )
    conflicts_empty = evaluator.evaluate(Timetable(assignments=[a1, a5]), context)
    assert len(conflicts_empty) == 1
    assert "change buildings from 'LH' to ''" in conflicts_empty[0].description


def test_constraint_set_scoring_and_normalization() -> None:
    """Test ConstraintSet evaluation, scoring, and normalization."""
    c_hard_def = Constraint(
        constraint_id="H01",
        name="Faculty Overlap",
        severity=Severity.HARD,
        weight=1.0,
    )
    c_soft_def1 = Constraint(
        constraint_id="S01",
        name="Morning Preference",
        severity=Severity.SOFT,
        weight=2.0,
    )
    c_soft_def2 = Constraint(
        constraint_id="S02",
        name="Balanced Workload",
        severity=Severity.SOFT,
        weight=3.0,
    )

    eval_hard = FacultyOverlapConstraint(c_hard_def)
    eval_soft1 = MorningPreferenceConstraint(c_soft_def1)
    eval_soft2 = BalancedWorkloadConstraint(c_soft_def2)

    c_set = ConstraintSet([eval_hard, eval_soft1, eval_soft2])

    # Test weight normalization
    c_set.normalize_weights()
    assert eval_soft1.definition.weight == pytest.approx(2.0 / 5.0)
    assert eval_soft2.definition.weight == pytest.approx(3.0 / 5.0)

    # Setup timetable and context to trigger a soft violation (afternoon class)
    s_afternoon = Slot(
        slot_id="S02",
        day=Day.MONDAY,
        start_time=datetime.time(14, 0),
        end_time=datetime.time(15, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s_afternoon]
    )
    a_afternoon = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S02",
        room_id="R1",
    )
    timetable = Timetable(assignments=[a_afternoon])

    # Evaluate list of conflicts
    all_conflicts = c_set.evaluate(timetable, context)
    assert len(all_conflicts) == 1

    # Soft violation expected on morning preference
    score = c_set.score(timetable, context)
    assert score.hard_violations == 0
    # soft_penalty = 1 violation * normalized weight (2/5 = 0.4)
    assert score.soft_score == pytest.approx(-0.4)
    assert score.overall_score == pytest.approx(-0.4)


def test_builder_build() -> None:
    """Test ConstraintBuilder building ConstraintSet from definitions."""
    definitions = [
        Constraint(
            constraint_id="H01",
            name="Faculty Overlap",
            severity=Severity.HARD,
            weight=1.0,
        ),
        Constraint(
            constraint_id="S01",
            name="Morning Preference",
            severity=Severity.SOFT,
            weight=2.0,
        ),
    ]
    c_set = ConstraintBuilder.build(definitions)
    assert isinstance(c_set, ConstraintSet)
    assert len(c_set.evaluators) == 2
    assert isinstance(c_set.evaluators[0], FacultyOverlapConstraint)
    assert isinstance(c_set.evaluators[1], MorningPreferenceConstraint)

    # Test room capacity negative check bypass
    class MockRoom:
        room_id = "R_BAD"
        capacity = -5
        room_type = RoomType.THEORY

    bad_room = cast(Room, MockRoom())
    assert bad_room.capacity == -5
