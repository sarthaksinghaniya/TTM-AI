"""Tests for HanuPlanner Brain models."""

import datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from brain.models import (
    Assignment,
    Conflict,
    Constraint,
    ConstraintError,
    Day,
    Faculty,
    GraphBuildError,
    Room,
    RoomType,
    ScheduleScore,
    SchedulingError,
    Section,
    Severity,
    Slot,
    Subject,
    Timetable,
    ValidationError,
)


def test_custom_exceptions() -> None:
    """Verify custom exceptions can be initialized with multiple arguments."""
    err = ValidationError("FAC01", "Faculty unavailable all week")
    assert err.args == ("FAC01", "Faculty unavailable all week")

    err_c = ConstraintError("CONST01", "Constraint violation")
    assert err_c.args == ("CONST01", "Constraint violation")

    err_g = GraphBuildError("GRAPH01", "Graph build failed")
    assert err_g.args == ("GRAPH01", "Graph build failed")

    err_s = SchedulingError("SCHED01", "Scheduling execution failed")
    assert err_s.args == ("SCHED01", "Scheduling execution failed")


def test_faculty_validation() -> None:
    """Test Faculty model validation, immutability, and forbid extra fields."""
    faculty = Faculty(
        faculty_id="FAC001",
        name="Dr. Smith",
        department="Computer Science",
        max_lectures_per_day=3,
        preferred_slots=["SLOT01"],
        unavailable_slots=["SLOT02"],
    )
    assert faculty.faculty_id == "FAC001"
    assert faculty.name == "Dr. Smith"
    assert faculty.max_lectures_per_day == 3

    # Test frozen
    with pytest.raises(PydanticValidationError):
        faculty.name = "Dr. Jones"  # type: ignore

    # Test extra forbidden
    with pytest.raises(PydanticValidationError):
        Faculty(
            faculty_id="FAC001",
            name="Dr. Smith",
            department="CS",
            max_lectures_per_day=3,
            extra_field="not allowed",  # type: ignore
        )

    # Test empty string validation
    with pytest.raises(ValidationError):
        Faculty(
            faculty_id="",
            name="Dr. Smith",
            department="CS",
            max_lectures_per_day=3,
        )

    # Test negative max lectures validation
    with pytest.raises(ValidationError):
        Faculty(
            faculty_id="FAC001",
            name="Dr. Smith",
            department="CS",
            max_lectures_per_day=-1,
        )

    # Test empty strings in preferred slots
    with pytest.raises(ValidationError):
        Faculty(
            faculty_id="FAC001",
            name="Dr. Smith",
            department="CS",
            max_lectures_per_day=3,
            preferred_slots=[""],
        )


def test_subject_validation() -> None:
    """Test Subject model validation and boundaries."""
    subject = Subject(
        subject_code="CS101",
        subject_name="Intro to CS",
        credits=4,
        theory_hours=3,
        lab_hours=2,
        tutorial_hours=1,
        continuous_lab=True,
    )
    assert subject.subject_code == "CS101"
    assert subject.continuous_lab is True

    # Test negative hours validation
    with pytest.raises(ValidationError):
        Subject(
            subject_code="CS101",
            subject_name="Intro to CS",
            credits=4,
            theory_hours=-1,
            lab_hours=2,
            tutorial_hours=1,
            continuous_lab=True,
        )

    # Test empty string validation
    with pytest.raises(ValidationError):
        Subject(
            subject_code=" ",
            subject_name="Intro to CS",
            credits=4,
            theory_hours=3,
            lab_hours=2,
            tutorial_hours=1,
            continuous_lab=True,
        )


def test_room_validation() -> None:
    """Test Room model validation and RoomType enum."""
    room = Room(room_id="R101", capacity=50, room_type=RoomType.THEORY)
    assert room.room_id == "R101"
    assert room.room_type == RoomType.THEORY

    # Test zero or negative capacity validation
    with pytest.raises(ValidationError):
        Room(room_id="R101", capacity=0, room_type=RoomType.THEORY)

    # Test empty room_id validation
    with pytest.raises(ValidationError):
        Room(room_id="", capacity=50, room_type=RoomType.THEORY)


def test_section_validation() -> None:
    """Test Section model validation."""
    section = Section(section_id="SEC_A", program="CS", year=1, strength=40)
    assert section.section_id == "SEC_A"

    # Test non-positive strength validation
    with pytest.raises(ValidationError):
        Section(section_id="SEC_A", program="CS", year=1, strength=0)

    # Test non-positive year validation
    with pytest.raises(ValidationError):
        Section(section_id="SEC_A", program="CS", year=0, strength=40)

    # Test empty string validation
    with pytest.raises(ValidationError):
        Section(section_id="SEC_A", program=" ", year=1, strength=40)


def test_slot_validation() -> None:
    """Test Slot model validation, Day enum, and time range checks."""
    slot = Slot(
        slot_id="S01",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    assert slot.slot_id == "S01"
    assert slot.day == Day.MONDAY

    # Test end_time <= start_time
    with pytest.raises(ValidationError):
        Slot(
            slot_id="S01",
            day=Day.MONDAY,
            start_time=datetime.time(10, 0),
            end_time=datetime.time(9, 0),
        )

    # Test empty slot_id validation
    with pytest.raises(ValidationError):
        Slot(
            slot_id="",
            day=Day.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )


def test_assignment_validation() -> None:
    """Test Assignment model validation."""
    assignment = Assignment(
        assignment_id="A01",
        section_id="SEC_A",
        faculty_id="FAC001",
        subject_code="CS101",
        slot_id="S01",
        room_id="R101",
    )
    assert assignment.assignment_id == "A01"

    # Test empty field validation
    with pytest.raises(ValidationError):
        Assignment(
            assignment_id="A01",
            section_id=" ",
            faculty_id="FAC001",
            subject_code="CS101",
            slot_id="S01",
            room_id="R101",
        )


def test_constraint_validation() -> None:
    """Test Constraint model validation and severity enum."""
    constraint = Constraint(
        constraint_id="C01",
        name="No Faculty Clash",
        severity=Severity.HARD,
        weight=1.0,
    )
    assert constraint.constraint_id == "C01"
    assert constraint.severity == Severity.HARD

    # Test negative weight validation
    with pytest.raises(ValidationError):
        Constraint(
            constraint_id="C01",
            name="No Faculty Clash",
            severity=Severity.HARD,
            weight=-0.5,
        )

    # Test empty constraint_id validation
    with pytest.raises(ValidationError):
        Constraint(
            constraint_id="",
            name="No Faculty Clash",
            severity=Severity.HARD,
            weight=1.0,
        )


def test_conflict_validation() -> None:
    """Test Conflict model validation."""
    conflict = Conflict(
        conflict_id="CF01",
        description="Double booking",
        severity=Severity.HARD,
        suggestion="Reschedule one class",
    )
    assert conflict.conflict_id == "CF01"

    # Test empty conflict fields
    with pytest.raises(ValidationError):
        Conflict(
            conflict_id="CF01",
            description="",
            severity=Severity.HARD,
            suggestion="Reschedule one class",
        )


def test_timetable_operations() -> None:
    """Test Timetable get_schedule, serialize, and deserialize methods."""
    a1 = Assignment(
        assignment_id="A01",
        section_id="SEC_A",
        faculty_id="FAC001",
        subject_code="CS101",
        slot_id="S01",
        room_id="R101",
    )
    a2 = Assignment(
        assignment_id="A02",
        section_id="SEC_B",
        faculty_id="FAC001",
        subject_code="CS102",
        slot_id="S02",
        room_id="R102",
    )
    timetable = Timetable(assignments=[a1, a2])

    # Test schedule filtering
    fac_schedule = timetable.get_faculty_schedule("FAC001")
    assert len(fac_schedule) == 2
    assert a1 in fac_schedule
    assert a2 in fac_schedule

    room_schedule = timetable.get_room_schedule("R101")
    assert len(room_schedule) == 1
    assert room_schedule[0] == a1

    sec_schedule = timetable.get_section_schedule("SEC_B")
    assert len(sec_schedule) == 1
    assert sec_schedule[0] == a2

    # Test serialization
    serialized = timetable.serialize()
    assert "A01" in serialized
    assert "A02" in serialized

    # Test deserialization
    deserialized = Timetable.deserialize(serialized)
    assert len(deserialized.assignments) == 2
    assert deserialized.assignments[0].assignment_id == "A01"

    # Test failed deserialization
    with pytest.raises(ValidationError):
        Timetable.deserialize("invalid json")


@pytest.mark.parametrize(
    "hard_violations,soft_score,expected_norm,expected_grade",
    [
        (1, -50.0, 0.0, "F"),
        (0, 0.0, 1.0, "A+"),
        (0, -0.05, 1.0 / 1.05, "A+"),  # 0.952
        (0, -0.15, 1.0 / 1.15, "A"),  # 0.869
        (0, -0.4, 1.0 / 1.4, "B"),  # 0.714
        (0, -0.9, 1.0 / 1.9, "C"),  # 0.526
        (0, -2.0, 1.0 / 3.0, "D"),  # 0.333
    ],
)
def test_schedule_score_logic(
    hard_violations: int,
    soft_score: float,
    expected_norm: float,
    expected_grade: str,
) -> None:
    """Verify normalized_score and grade logic across various combinations."""
    score = ScheduleScore(
        hard_violations=hard_violations,
        soft_score=soft_score,
        overall_score=0.0,  # placeholder
    )
    assert pytest.approx(score.normalized_score()) == expected_norm
    assert score.grade() == expected_grade


def test_schedule_score_validation() -> None:
    """Test validation errors for ScheduleScore."""
    with pytest.raises(ValidationError):
        ScheduleScore(hard_violations=-1, soft_score=0.0, overall_score=0.0)
