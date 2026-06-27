"""Tests for HanuPlanner Brain greedy scheduler."""

import datetime

from brain.constraints.base import ConstraintContext
from brain.models import (
    Assignment,
    Day,
    Room,
    RoomType,
    Section,
    Slot,
    Timetable,
)
from brain.scheduler.greedy_scheduler import GreedyScheduler


def test_scheduler_empty_timetable() -> None:
    """Test scheduling an empty timetable."""
    scheduler = GreedyScheduler()
    t = Timetable(assignments=[])
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 0
    assert len(result.locked_assignments) == 0
    assert len(result.unscheduled_assignments) == 0
    assert result.statistics.failed_count == 0
    assert result.statistics.success_rate == 1.0
    assert result.statistics.runtime_ms >= 0.0


def test_scheduler_no_slots_fails() -> None:
    """Test scheduling fails when no slots are available in context."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 0
    assert len(result.unscheduled_assignments) == 1
    assert result.unscheduled_assignments[0].assignment_id == "A1"
    assert result.statistics.failed_count == 1
    assert result.statistics.success_rate == 0.0


def test_scheduler_no_rooms_fails() -> None:
    """Test scheduling fails when no rooms are available in context."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 0
    assert len(result.unscheduled_assignments) == 1
    assert result.statistics.failed_count == 1
    assert result.statistics.success_rate == 0.0


def test_scheduler_successful_single() -> None:
    """Test successfully scheduling a single assignment."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 1
    assert len(result.unscheduled_assignments) == 0
    assert result.statistics.failed_count == 0
    assert result.statistics.success_rate == 1.0

    scheduled = result.partial_timetable.assignments[0]
    assert scheduled.assignment_id == "A1"
    assert scheduled.slot_id == "S1"
    assert scheduled.room_id == "R1"


def test_scheduler_faculty_clash_prevented() -> None:
    """Test that two assignments sharing a faculty are scheduled in different slots."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
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
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 2
    assert len(result.unscheduled_assignments) == 0
    s_ids = {a.slot_id for a in result.partial_timetable.assignments}
    assert s_ids == {"S1", "S2"}


def test_scheduler_section_clash_prevented() -> None:
    """Test that two assignments sharing a section are scheduled in different slots."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
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
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 2
    assert len(result.unscheduled_assignments) == 0
    s_ids = {a.slot_id for a in result.partial_timetable.assignments}
    assert s_ids == {"S1", "S2"}


def test_scheduler_room_clash_prevented() -> None:
    """Test that two assignments scheduled in the same slot occupy different rooms."""
    scheduler = GreedyScheduler()
    # Faculty and Section are distinct, so they can be scheduled in the same slot.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1, r2], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 2
    assert len(result.unscheduled_assignments) == 0
    r_ids = {a.room_id for a in result.partial_timetable.assignments}
    assert r_ids == {"R1", "R2"}


def test_scheduler_holiday_bypassed() -> None:
    """Test that slots marked as holidays are bypassed by the scheduler."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1], holidays=["S1"]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 0
    assert len(result.unscheduled_assignments) == 1
    assert result.statistics.failed_count == 1


def test_scheduler_room_capacity_check() -> None:
    """Test room selection checks section strength limits."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_LARGE",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    # R1 is too small. R2 is large enough.
    r1 = Room(room_id="R1_SMALL", capacity=20, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2_LARGE", capacity=60, room_type=RoomType.THEORY)
    sec = Section(section_id="SEC_LARGE", program="CS", year=1, strength=45)
    context = ConstraintContext(
        faculties=[],
        rooms=[r1, r2],
        subjects=[],
        sections=[sec],
        slots=[s1],
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 1
    assert result.partial_timetable.assignments[0].room_id == "R2_LARGE"


def test_scheduler_mrv_priority() -> None:
    """Test that assignments with fewer available slots (MRV) are prioritized."""
    scheduler = GreedyScheduler()
    # A1 can only go to S1 (because F1 is busy in S2 due to a locked assignment)
    # A2 has no faculty conflicts, so it can go to S1 or S2.
    # Therefore, A1 should have fewer feasible slots (1 vs 2) and should be
    # scheduled first.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    locked = Assignment(
        assignment_id="LOCKED",
        section_id="SEC_C",
        faculty_id="F1",
        subject_code="CS103",
        slot_id="S2",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, a2, locked])

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
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1, r2], subjects=[], sections=[], slots=[s1, s2]
    )

    result = scheduler.schedule(t, context, locked_assignment_ids={"LOCKED"})
    assert len(result.partial_timetable.assignments) == 3
    # Check that A1 successfully claimed S1 (since S2 was locked for F1)
    a1_sched = next(
        a for a in result.partial_timetable.assignments if a.assignment_id == "A1"
    )
    assert a1_sched.slot_id == "S1"


def test_scheduler_degree_priority_tie_break() -> None:
    """Test high degree in conflict graph breaks tie in selection priority."""
    scheduler = GreedyScheduler()
    # A1 conflicts with A2 and A3 (via F1). A1 has degree 2.
    # A2 only conflicts with A1. A2 has degree 1.
    # A3 only conflicts with A1. A3 has degree 1.
    # Since all start with equal domain size, A1 (highest degree) should be
    # scheduled first.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_C",
        faculty_id="F1",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])

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
    s3 = Slot(
        slot_id="S3",
        day=Day.MONDAY,
        start_time=datetime.time(11, 0),
        end_time=datetime.time(12, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2, s3]
    )

    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 3
    # A1 (highest degree) scheduled first, getting earliest slot S1
    a1_sched = next(
        a for a in result.partial_timetable.assignments if a.assignment_id == "A1"
    )
    assert a1_sched.slot_id == "S1"


def test_scheduler_locked_assignments_preserved() -> None:
    """Test that locked assignments are preserved as-is."""
    scheduler = GreedyScheduler()
    locked = Assignment(
        assignment_id="LOCKED",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S2",
        room_id="R2",
    )
    t = Timetable(assignments=[locked])
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )
    result = scheduler.schedule(t, context, locked_assignment_ids={"LOCKED"})
    assert len(result.locked_assignments) == 1
    assert result.locked_assignments[0] == locked
    assert len(result.partial_timetable.assignments) == 1
    assert result.partial_timetable.assignments[0] == locked


def test_scheduler_locked_prevents_unlocked_sharing() -> None:
    """Test that locked assignments block conflicting allocations."""
    scheduler = GreedyScheduler()
    # A1 shares faculty F1 with LOCKED. Since LOCKED is at S1, A1 must get S2.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    locked = Assignment(
        assignment_id="LOCKED",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, locked])

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
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2]
    )

    result = scheduler.schedule(t, context, locked_assignment_ids={"LOCKED"})
    a1_sched = next(
        a for a in result.partial_timetable.assignments if a.assignment_id == "A1"
    )
    assert a1_sched.slot_id == "S2"


def test_scheduler_failed_count_incremented() -> None:
    """Test that failed count increments when an assignment is unfeasible."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    # Impossible capacity requirement
    sec = Section(section_id="SEC_A", program="CS", year=1, strength=100)
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[sec], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert len(result.unscheduled_assignments) == 1
    assert result.statistics.failed_count == 1
    assert result.statistics.success_rate == 0.0


def test_scheduler_success_rate_calculation() -> None:
    """Test success_rate calculation when some succeed and some fail."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",  # Shares section, clashes!
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    # Only 1 slot is available, so only 1 can succeed, other must fail!
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert result.statistics.failed_count == 1
    assert result.statistics.success_rate == 0.5


def test_scheduler_runtime_ms_recorded() -> None:
    """Test runtime_ms is recorded correctly."""
    scheduler = GreedyScheduler()
    t = Timetable(assignments=[])
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )
    result = scheduler.schedule(t, context)
    assert result.statistics.runtime_ms >= 0.0


def test_scheduler_earliest_slot_selected() -> None:
    """Test that the earliest slot is selected first."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    # Tuesday slot vs Monday slot. Monday slot is earlier.
    s_mon = Slot(
        slot_id="S_MON",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s_tue = Slot(
        slot_id="S_TUE",
        day=Day.TUESDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s_tue, s_mon]
    )
    result = scheduler.schedule(t, context)
    assert result.partial_timetable.assignments[0].slot_id == "S_MON"


def test_scheduler_lexicographical_tie_break() -> None:
    """Test lexicographical tie-break ordering on assignment IDs."""
    scheduler = GreedyScheduler()
    # A_FIRST and B_SECOND are identical. A_FIRST should be selected first
    # due to sorting.
    a1 = Assignment(
        assignment_id="B_SECOND",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A_FIRST",
        section_id="SEC_A",  # shared section
        faculty_id="F1",  # shared faculty
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    # A_FIRST should occupy the only slot S1
    assert result.partial_timetable.assignments[0].assignment_id == "A_FIRST"
    assert result.partial_timetable.assignments[0].slot_id == "S1"
    assert len(result.unscheduled_assignments) == 1
    assert result.unscheduled_assignments[0].assignment_id == "B_SECOND"


def test_scheduler_empty_unlocked_success_rate() -> None:
    """Test scheduling 0 unlocked assignments returns success rate of 1.0."""
    scheduler = GreedyScheduler()
    locked = Assignment(
        assignment_id="LOCKED",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    t = Timetable(assignments=[locked])
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )
    result = scheduler.schedule(t, context, locked_assignment_ids={"LOCKED"})
    assert result.statistics.success_rate == 1.0


def test_scheduler_extreme_over_allocation() -> None:
    """Test extreme resource allocation failure limits."""
    scheduler = GreedyScheduler()
    # 20 assignments, but only 1 slot. At most 1 can succeed, 19 must fail.
    assignments = [
        Assignment(
            assignment_id=f"A{i}",
            section_id="SEC_A",  # same section
            faculty_id="F1",
            subject_code="CS101",
            slot_id="UNASSIGNED",
            room_id="UNASSIGNED",
        )
        for i in range(20)
    ]
    t = Timetable(assignments=assignments)
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = scheduler.schedule(t, context)
    assert len(result.partial_timetable.assignments) == 1
    assert len(result.unscheduled_assignments) == 19
    assert result.statistics.failed_count == 19
    assert result.statistics.success_rate == 0.05


def test_scheduler_unlocked_domain_reduction_by_locked() -> None:
    """Test that locked assignments reduce the domains of unlocked ones."""
    scheduler = GreedyScheduler()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",  # shares section with LOCKED
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    locked = Assignment(
        assignment_id="LOCKED",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, locked])
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
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2]
    )
    result = scheduler.schedule(t, context, locked_assignment_ids={"LOCKED"})
    assert len(result.partial_timetable.assignments) == 2
    a1_sched = next(
        a for a in result.partial_timetable.assignments if a.assignment_id == "A1"
    )
    assert a1_sched.slot_id == "S2"
