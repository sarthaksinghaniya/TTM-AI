"""Tests for HanuPlanner Brain refactored domain models."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from brain.models import (
    Assignment,
    Curriculum,
    Day,
    ScheduledAssignment,
    TeachingRequirement,
    ValidationError,
)


def test_teaching_requirement_valid() -> None:
    """Test valid construction of TeachingRequirement."""
    req = TeachingRequirement(
        requirement_id="REQ_01",
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=["C_01", "C_02"],
    )
    assert req.requirement_id == "REQ_01"
    assert req.weekly_theory_hours == 3
    assert req.weekly_lab_hours == 2
    assert req.constraint_refs == ["C_01", "C_02"]


def test_teaching_requirement_empty_id() -> None:
    """Test empty requirement_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="  ",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_faculty() -> None:
    """Test empty faculty_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="  ",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_section() -> None:
    """Test empty section_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id=" ",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_subject() -> None:
    """Test empty subject_code fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_room_type() -> None:
    """Test empty preferred_room_type fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="\t",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_batch() -> None:
    """Test empty batch fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="",
            constraint_refs=[],
        )


def test_teaching_requirement_negative_theory_hours() -> None:
    """Test negative weekly_theory_hours fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=-1,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_negative_lab_hours() -> None:
    """Test negative weekly_lab_hours fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=-5,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
        )


def test_teaching_requirement_empty_constraint_ref() -> None:
    """Test constraint_refs list with empty string element fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=["C_01", "  "],
        )


def test_teaching_requirement_immutability() -> None:
    """Test that TeachingRequirement is frozen."""
    req = TeachingRequirement(
        requirement_id="REQ_01",
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    with pytest.raises(PydanticValidationError):
        # Pydantic frozen model raises ValidationError when mutating
        req.weekly_theory_hours = 4  # type: ignore[misc]


def test_teaching_requirement_extra_forbid() -> None:
    """Test extra fields are forbidden in TeachingRequirement."""
    with pytest.raises(PydanticValidationError):
        TeachingRequirement(
            requirement_id="REQ_01",
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="Batch A",
            constraint_refs=[],
            extra_field="value",  # type: ignore[call-arg]
        )


def test_scheduled_assignment_valid() -> None:
    """Test valid construction of ScheduledAssignment."""
    sched = ScheduledAssignment(
        session_id="S_01",
        day=Day.MONDAY,
        slot_id="SL_1",
        room_id="R_1",
        duration=2,
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
    )
    assert sched.session_id == "S_01"
    assert sched.day == Day.MONDAY
    assert sched.duration == 2


def test_scheduled_assignment_empty_session_id() -> None:
    """Test empty session_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id=" ",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=2,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_empty_slot_id() -> None:
    """Test empty slot_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="",
            room_id="R_1",
            duration=2,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_empty_room_id() -> None:
    """Test empty room_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id=" \t",
            duration=2,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_empty_faculty() -> None:
    """Test empty faculty_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=2,
            faculty_id="",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_empty_section() -> None:
    """Test empty section_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=2,
            faculty_id="F_01",
            section_id="",
            subject_code="CS101",
        )


def test_scheduled_assignment_empty_subject() -> None:
    """Test empty subject_code fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=2,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="  ",
        )


def test_scheduled_assignment_zero_duration() -> None:
    """Test zero duration fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=0,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_negative_duration() -> None:
    """Test negative duration fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=-3,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
        )


def test_scheduled_assignment_immutability() -> None:
    """Test that ScheduledAssignment is frozen."""
    sched = ScheduledAssignment(
        session_id="S_01",
        day=Day.MONDAY,
        slot_id="SL_1",
        room_id="R_1",
        duration=2,
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
    )
    with pytest.raises(PydanticValidationError):
        sched.duration = 4  # type: ignore[misc]


def test_scheduled_assignment_extra_forbid() -> None:
    """Test extra fields are forbidden in ScheduledAssignment."""
    with pytest.raises(PydanticValidationError):
        ScheduledAssignment(
            session_id="S_01",
            day=Day.MONDAY,
            slot_id="SL_1",
            room_id="R_1",
            duration=2,
            faculty_id="F_01",
            section_id="SEC_A",
            subject_code="CS101",
            extra="val",  # type: ignore[call-arg]
        )


def test_scheduled_assignment_migration_from_assignment() -> None:
    """Test migration utility from Assignment model."""
    a = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="SL_1",
        room_id="R_1",
    )
    sched = ScheduledAssignment.from_assignment(
        assignment=a, day=Day.WEDNESDAY, duration=3
    )
    assert sched.session_id == "A1"
    assert sched.day == Day.WEDNESDAY
    assert sched.slot_id == "SL_1"
    assert sched.room_id == "R_1"
    assert sched.duration == 3
    assert sched.faculty_id == "F1"
    assert sched.section_id == "SEC_A"
    assert sched.subject_code == "CS101"


def test_scheduled_assignment_migration_to_assignment() -> None:
    """Test conversion back to older Assignment layout."""
    sched = ScheduledAssignment(
        session_id="S_01",
        day=Day.THURSDAY,
        slot_id="SL_1",
        room_id="R_1",
        duration=1,
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
    )
    a = sched.to_assignment()
    assert a.assignment_id == "S_01"
    assert a.slot_id == "SL_1"
    assert a.room_id == "R_1"
    assert a.faculty_id == "F_01"
    assert a.section_id == "SEC_A"
    assert a.subject_code == "CS101"


def test_curriculum_valid() -> None:
    """Test valid construction of Curriculum."""
    req1 = TeachingRequirement(
        requirement_id="REQ_01",
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    req2 = TeachingRequirement(
        requirement_id="REQ_02",
        faculty_id="F_02",
        section_id="SEC_B",
        subject_code="CS102",
        weekly_theory_hours=4,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch B",
        constraint_refs=[],
    )
    cur = Curriculum(
        curriculum_id="CUR_01", name="CS Curriculum", requirements=[req1, req2]
    )
    assert cur.curriculum_id == "CUR_01"
    assert len(cur.requirements) == 2


def test_curriculum_empty_id() -> None:
    """Test empty curriculum_id fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        Curriculum(curriculum_id="  ", name="CS Curriculum", requirements=[])


def test_curriculum_empty_name() -> None:
    """Test empty name fails validation."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        Curriculum(curriculum_id="CUR_01", name="", requirements=[])


def test_curriculum_duplicate_requirements() -> None:
    """Test that duplicate requirements raise ValidationError."""
    req1 = TeachingRequirement(
        requirement_id="REQ_DUP",
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    req2 = TeachingRequirement(
        requirement_id="REQ_DUP",  # DUPLICATE ID
        faculty_id="F_02",
        section_id="SEC_B",
        subject_code="CS102",
        weekly_theory_hours=4,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch B",
        constraint_refs=[],
    )
    with pytest.raises((ValidationError, PydanticValidationError)):
        Curriculum(
            curriculum_id="CUR_01",
            name="CS Curriculum",
            requirements=[req1, req2],
        )


def test_curriculum_serialization_roundtrip() -> None:
    """Test serialization and deserialization roundtrip of Curriculum."""
    req = TeachingRequirement(
        requirement_id="REQ_01",
        faculty_id="F_01",
        section_id="SEC_A",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    cur = Curriculum(curriculum_id="CUR_01", name="CS Curriculum", requirements=[req])
    json_str = cur.model_dump_json()
    deserialized = Curriculum.model_validate_json(json_str)
    assert deserialized.curriculum_id == cur.curriculum_id
    assert deserialized.name == cur.name
    assert deserialized.requirements[0].requirement_id == "REQ_01"
