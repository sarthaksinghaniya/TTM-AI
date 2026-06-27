"""Tests for HanuPlanner Brain validation engine and validators."""

import datetime
from typing import Any, cast

import pytest

from brain.models import (
    Assignment,
    Day,
    Faculty,
    Room,
    RoomType,
    Section,
    Slot,
    Subject,
    Timetable,
    ValidationError,
)
from brain.validation import (
    CalendarValidator,
    CompositeValidator,
    FacultyValidator,
    RoomValidator,
    SectionValidator,
    SubjectValidator,
    TimetableValidator,
    ValidationResult,
)


@pytest.mark.asyncio
async def test_base_validator_enforce_and_async() -> None:
    """Test BaseValidator helper methods.

    Verifies validate_enforce, validate_many, and validate_async.
    """
    # Test valid enforcement
    val = RoomValidator()
    rooms = [Room(room_id="R101", capacity=30, room_type=RoomType.THEORY)]
    val.validate_enforce(rooms)

    # Test invalid enforcement raises ValidationError
    bad_rooms = [
        Room(room_id="R101", capacity=30, room_type=RoomType.THEORY),
        Room(room_id="R101", capacity=30, room_type=RoomType.THEORY),
    ]
    with pytest.raises(ValidationError) as exc:
        val.validate_enforce(bad_rooms)
    assert "Duplicate room ID found" in str(exc.value)

    # Test async validation
    res = await val.validate_async(rooms)
    assert res.is_valid is True

    bad_res = await val.validate_async(bad_rooms)
    assert bad_res.is_valid is False

    # Test validate_many
    res_many = val.validate_many([rooms, bad_rooms])
    assert res_many.is_valid is False
    assert len(res_many.errors) == 1
    assert "Duplicate room ID found" in res_many.errors[0]


def test_composite_validator() -> None:
    """Test CompositeValidator combining errors from multiple sub-validators."""
    val1 = RoomValidator()
    val2 = SubjectValidator()

    # Valid scenario
    composite = CompositeValidator([val1, val2])
    assert composite is not None

    class DummyValidator1(RoomValidator):
        def validate(self, data: Any) -> ValidationResult:
            return ValidationResult(is_valid=True)

    class DummyValidator2(RoomValidator):
        def validate(self, data: Any) -> ValidationResult:
            return ValidationResult(is_valid=False, errors=["Error from validator 2"])

    comp = CompositeValidator([DummyValidator1(), DummyValidator2()])
    res = comp.validate("some_data")
    assert res.is_valid is False
    assert len(res.errors) == 1
    assert res.errors[0] == "Error from validator 2"

    # Test unexpected error catching in CompositeValidator
    class BreakingValidator(RoomValidator):
        def validate(self, data: Any) -> ValidationResult:
            raise RuntimeError("Broken validator")

    comp_breaking = CompositeValidator([BreakingValidator()])
    breaking_res = comp_breaking.validate("some_data")
    assert breaking_res.is_valid is False
    assert "Unexpected validation error" in breaking_res.errors[0]


def test_faculty_validator() -> None:
    """Test FacultyValidator for duplicate IDs and full week unavailability."""
    all_slots = ["S01", "S02", "S03"]
    validator = FacultyValidator(all_slots=all_slots)

    # Valid
    f1 = Faculty(
        faculty_id="F1",
        name="Dr. Smith",
        department="CS",
        max_lectures_per_day=3,
        unavailable_slots=["S01"],
    )
    f2 = Faculty(
        faculty_id="F2",
        name="Dr. Jones",
        department="CS",
        max_lectures_per_day=3,
        unavailable_slots=["S02"],
    )
    res = validator.validate([f1, f2])
    assert res.is_valid is True

    # Duplicate IDs
    f3 = Faculty(
        faculty_id="F1",
        name="Dr. Alien",
        department="Math",
        max_lectures_per_day=3,
    )
    res_dup = validator.validate([f1, f3])
    assert res_dup.is_valid is False
    assert "Duplicate faculty ID found: 'F1'" in res_dup.errors

    # Unavailable all week
    f_lazy = Faculty(
        faculty_id="F_LAZY",
        name="Dr. Lazy",
        department="CS",
        max_lectures_per_day=0,
        unavailable_slots=["S01", "S02", "S03", "S04"],
    )
    res_lazy = validator.validate([f_lazy])
    assert res_lazy.is_valid is False
    assert "Faculty unavailable all week: F_LAZY" in res_lazy.errors


def test_room_validator() -> None:
    """Test RoomValidator duplicate and negative capacity checks."""
    validator = RoomValidator()

    # Valid
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=30, room_type=RoomType.LAB)
    res = validator.validate([r1, r2])
    assert res.is_valid is True

    # Duplicate IDs
    r3 = Room(room_id="R1", capacity=25, room_type=RoomType.TUTORIAL)
    res_dup = validator.validate([r1, r3])
    assert res_dup.is_valid is False
    assert "Duplicate room ID found: 'R1'" in res_dup.errors

    class MockRoom:
        room_id = "R_BAD"
        capacity = -5
        room_type = RoomType.THEORY

    bad_room = cast(Room, MockRoom())
    res_bad = validator.validate([bad_room])
    assert res_bad.is_valid is False
    assert "Room 'R_BAD' capacity must be positive: got -5" in res_bad.errors


def test_subject_validator() -> None:
    """Test SubjectValidator for duplicate codes and credits mismatch."""
    validator = SubjectValidator()

    # Valid
    s1 = Subject(
        subject_code="CS101",
        subject_name="Intro to CS",
        credits=5,
        theory_hours=3,
        lab_hours=2,
        tutorial_hours=1,
        continuous_lab=False,
    )
    res = validator.validate([s1])
    assert res.is_valid is True

    # Credits mismatch
    s2 = Subject(
        subject_code="CS102",
        subject_name="Data Structures",
        credits=3,
        theory_hours=3,
        lab_hours=2,
        tutorial_hours=1,
        continuous_lab=False,
    )
    res_mismatch = validator.validate([s2])
    assert res_mismatch.is_valid is False
    assert "Credits mismatch for subject 'CS102'" in res_mismatch.errors[0]

    # Duplicate subject codes
    s3 = Subject(
        subject_code="CS101",
        subject_name="Advanced CS",
        credits=5,
        theory_hours=3,
        lab_hours=2,
        tutorial_hours=1,
        continuous_lab=False,
    )
    res_dup = validator.validate([s1, s3])
    assert res_dup.is_valid is False
    assert "Duplicate subject code found: 'CS101'" in res_dup.errors


def test_calendar_validator() -> None:
    """Test CalendarValidator holiday overlap checks."""
    validator = CalendarValidator(holidays=["SLOT_NEW_YEAR"])

    # Valid assignment
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="SLOT_NORMAL",
        room_id="R1",
    )
    res = validator.validate([a1])
    assert res.is_valid is True

    # Overlap with holiday
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="SLOT_NEW_YEAR",
        room_id="R1",
    )
    res_overlap = validator.validate([a2])
    assert res_overlap.is_valid is False
    assert (
        "Holiday overlap: assignment 'A2' is scheduled on holiday slot 'SLOT_NEW_YEAR'"
        in res_overlap.errors
    )


def test_section_validator() -> None:
    """Test SectionValidator room capacity mismatch checks."""
    sec = Section(section_id="SEC_A", program="CS", year=1, strength=50)
    room = Room(room_id="R1", capacity=30, room_type=RoomType.THEORY)

    validator = SectionValidator(sections=[sec], rooms=[room])

    # Over-capacity assignment
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    res = validator.validate([a1])
    assert res.is_valid is False
    assert any(
        "Strength exceeds capacity" in error
        and "strength 50" in error
        and "capacity 30" in error
        for error in res.errors
    )

    # Valid capacity assignment
    room_big = Room(room_id="R_BIG", capacity=60, room_type=RoomType.THEORY)
    validator_valid = SectionValidator(sections=[sec], rooms=[room_big])
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R_BIG",
    )
    res_valid = validator_valid.validate([a2])
    assert res_valid.is_valid is True


def test_timetable_validator() -> None:
    """Test master TimetableValidator executing complete validation suite."""
    fac = Faculty(
        faculty_id="F1",
        name="Dr. Smith",
        department="CS",
        max_lectures_per_day=3,
    )
    room = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    sub = Subject(
        subject_code="CS101",
        subject_name="Intro to CS",
        credits=3,
        theory_hours=3,
        lab_hours=0,
        tutorial_hours=0,
        continuous_lab=False,
    )
    sec = Section(section_id="SEC_A", program="CS", year=1, strength=40)
    slot = Slot(
        slot_id="S01",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )

    validator = TimetableValidator(
        faculties=[fac],
        rooms=[room],
        subjects=[sub],
        sections=[sec],
        slots=[slot],
        holidays=["S01"],
    )

    # Valid assignments but calendar clashes with holiday
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S01",
        room_id="R1",
    )
    timetable = Timetable(assignments=[a1])

    res = validator.validate(timetable)
    assert res.is_valid is False
    assert len(res.errors) == 1
    assert "Holiday overlap" in res.errors[0]
