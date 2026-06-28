"""Tests for HanuPlanner Brain SchedulingInstance framework."""

import datetime
from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from brain.models import (
    Day,
    Faculty,
    Room,
    RoomType,
    Section,
    Slot,
    Subject,
    TeachingRequirement,
    ValidationError,
)
from brain.problem import (
    InstanceSerializer,
    SchedulingInstance,
    SchedulingInstanceBuilder,
)
from brain.session import SessionType, TeachingSession


@pytest.fixture
def sample_data() -> dict[str, Any]:
    """Sample valid data elements for builders."""
    f1 = Faculty(
        faculty_id="F1", name="Faculty 1", department="CS", max_lectures_per_day=4
    )
    s1 = Subject(
        subject_code="CS101",
        subject_name="CS I",
        credits=4,
        theory_hours=4,
        lab_hours=0,
        tutorial_hours=0,
        continuous_lab=False,
    )
    r1 = Room(room_id="R1", capacity=30, room_type=RoomType.THEORY)
    sec1 = Section(section_id="SEC1", program="CS", year=1, strength=25)
    slot1 = Slot(
        slot_id="SL1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    req1 = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=3,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sess1 = TeachingSession(
        session_id="CS101_T1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
    )
    return {
        "faculties": [f1],
        "subjects": [s1],
        "rooms": [r1],
        "sections": [sec1],
        "slots": [slot1],
        "holidays": ["SL100"],
        "requirements": [req1],
        "sessions": [sess1],
        "config": {"debug": True},
        "metadata": {"author": "Antigravity"},
    }


def test_builder_empty() -> None:
    """Test default builder generates empty valid instance."""
    builder = SchedulingInstanceBuilder()
    instance = builder.build()
    assert isinstance(instance, SchedulingInstance)
    assert len(instance.faculties) == 0
    assert len(instance.subjects) == 0


def test_builder_valid_fluent(sample_data: dict[str, Any]) -> None:
    """Test successful build using fluent setter pipeline."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_holidays(sample_data["holidays"])
        .set_requirements(sample_data["requirements"])
        .set_sessions(sample_data["sessions"])
        .set_config(sample_data["config"])
        .set_metadata(sample_data["metadata"])
        .set_constraint_set("SampleConstraintSet")
    )
    instance = builder.build()
    assert len(instance.faculties) == 1
    assert len(instance.holidays) == 1
    assert instance.constraint_set == "SampleConstraintSet"
    assert instance.config["debug"] is True


def test_instance_immutability_faculties(sample_data: dict[str, Any]) -> None:
    """Test that modifying instance fields fails validation (frozen)."""
    builder = SchedulingInstanceBuilder().set_faculties(sample_data["faculties"])
    instance = builder.build()
    with pytest.raises(PydanticValidationError):
        instance.config = {}  # type: ignore[misc]


def test_instance_hashability(sample_data: dict[str, Any]) -> None:
    """Test that SchedulingInstance is hashable."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_config(sample_data["config"])
    )
    inst1 = builder.build()
    inst2 = builder.build()
    s = {inst1, inst2}
    assert len(s) == 1  # Only 1 unique hash item added
    d = {inst1: "value"}
    assert d[inst2] == "value"


def test_instance_equality(sample_data: dict[str, Any]) -> None:
    """Test comparison logic."""
    builder = SchedulingInstanceBuilder().set_faculties(sample_data["faculties"])
    inst1 = builder.build()
    inst2 = builder.build()
    assert inst1 == inst2
    assert inst1 != "NotAnInstance"


def test_instance_cloning_no_updates(sample_data: dict[str, Any]) -> None:
    """Test clone returns an equivalent copy."""
    builder = SchedulingInstanceBuilder().set_faculties(sample_data["faculties"])
    inst = builder.build()
    cloned = inst.clone()
    assert cloned == inst


def test_instance_cloning_with_updates(sample_data: dict[str, Any]) -> None:
    """Test clone updates fields correctly."""
    builder = SchedulingInstanceBuilder().set_faculties(sample_data["faculties"])
    inst = builder.build()
    new_f = Faculty(
        faculty_id="F2", name="Faculty 2", department="CS", max_lectures_per_day=4
    )
    cloned = inst.clone(faculties=[new_f])
    assert len(cloned.faculties) == 1
    assert cloned.faculties[0].faculty_id == "F2"


def test_instance_serialization_roundtrip(sample_data: dict[str, Any]) -> None:
    """Test serializer round-trip."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions(sample_data["sessions"])
    )
    inst = builder.build()
    serializer = InstanceSerializer()
    json_str = serializer.serialize(inst)
    deserialized = serializer.deserialize(json_str)
    assert deserialized == inst


def test_instance_statistics(sample_data: dict[str, Any]) -> None:
    """Test statistics dictionary counts."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions(sample_data["sessions"])
    )
    inst = builder.build()
    stats = inst.statistics()
    assert stats["faculties_count"] == 1
    assert stats["total_demand_duration"] == 1


def test_instance_summary(sample_data: dict[str, Any]) -> None:
    """Test summary formatted representation."""
    builder = SchedulingInstanceBuilder()
    inst = builder.build()
    summary = inst.summary()
    assert "HanuPlanner Brain Scheduling Instance Summary" in summary


def test_validator_duplicate_faculty() -> None:
    """Test duplicate faculty IDs raise validation error."""
    f1 = Faculty(
        faculty_id="F1", name="Faculty 1", department="CS", max_lectures_per_day=4
    )
    f2 = Faculty(
        faculty_id="F1", name="Faculty 2", department="CS", max_lectures_per_day=4
    )
    builder = SchedulingInstanceBuilder().set_faculties([f1, f2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'F1'" in str(exc.value)


def test_validator_duplicate_subject() -> None:
    """Test duplicate subject codes raise validation error."""
    s1 = Subject(
        subject_code="CS101",
        subject_name="CS 1",
        credits=3,
        theory_hours=3,
        lab_hours=0,
        tutorial_hours=0,
        continuous_lab=False,
    )
    s2 = Subject(
        subject_code="CS101",
        subject_name="CS 2",
        credits=3,
        theory_hours=3,
        lab_hours=0,
        tutorial_hours=0,
        continuous_lab=False,
    )
    builder = SchedulingInstanceBuilder().set_subjects([s1, s2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'CS101'" in str(exc.value)


def test_validator_duplicate_room() -> None:
    """Test duplicate room IDs raise validation error."""
    r1 = Room(room_id="R1", capacity=30, room_type=RoomType.THEORY)
    r2 = Room(room_id="R1", capacity=40, room_type=RoomType.THEORY)
    builder = SchedulingInstanceBuilder().set_rooms([r1, r2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'R1'" in str(exc.value)


def test_validator_duplicate_section() -> None:
    """Test duplicate section IDs raise validation error."""
    sec1 = Section(section_id="S1", program="CS", year=1, strength=20)
    sec2 = Section(section_id="S1", program="IT", year=1, strength=25)
    builder = SchedulingInstanceBuilder().set_sections([sec1, sec2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'S1'" in str(exc.value)


def test_validator_duplicate_slot() -> None:
    """Test duplicate slot IDs raise validation error."""
    slot1 = Slot(
        slot_id="SL1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    slot2 = Slot(
        slot_id="SL1",
        day=Day.TUESDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    builder = SchedulingInstanceBuilder().set_slots([slot1, slot2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'SL1'" in str(exc.value)


def test_validator_duplicate_requirement() -> None:
    """Test duplicate requirement IDs raise validation error."""
    req1 = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="S1",
        subject_code="C1",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="A",
        constraint_refs=[],
    )
    req2 = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="S1",
        subject_code="C1",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="A",
        constraint_refs=[],
    )
    builder = SchedulingInstanceBuilder().set_requirements([req1, req2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'REQ1'" in str(exc.value)


def test_validator_duplicate_session() -> None:
    """Test duplicate session IDs raise validation error."""
    sess1 = TeachingSession(
        session_id="SESS1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="S1",
        subject_code="C1",
    )
    sess2 = TeachingSession(
        session_id="SESS1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="S1",
        subject_code="C1",
    )
    builder = SchedulingInstanceBuilder().set_sessions([sess1, sess2])
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "Duplicate identifier 'SESS1'" in str(exc.value)


def test_validator_requirement_missing_faculty(sample_data: dict[str, Any]) -> None:
    """Test requirement referencing missing faculty ID fails."""
    # Remove faculty F1 from faculties list
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties([])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent faculty 'F1'" in str(exc.value)


def test_validator_requirement_missing_section(sample_data: dict[str, Any]) -> None:
    """Test requirement referencing missing section ID fails."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections([])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent section 'SEC1'" in str(exc.value)


def test_validator_requirement_missing_subject(sample_data: dict[str, Any]) -> None:
    """Test requirement referencing missing subject code fails."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects([])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent subject 'CS101'" in str(exc.value)


def test_validator_session_missing_requirement(sample_data: dict[str, Any]) -> None:
    """Test session referencing missing requirement ID fails."""
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements([])
        .set_sessions(sample_data["sessions"])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent requirement 'REQ1'" in str(exc.value)


def test_validator_session_missing_faculty(sample_data: dict[str, Any]) -> None:
    """Test session referencing missing faculty ID fails."""
    invalid_sess = TeachingSession(
        session_id="CS101_T1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F_MISSING",
        section_id="SEC1",
        subject_code="CS101",
    )
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions([invalid_sess])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent faculty 'F_MISSING'" in str(exc.value)


def test_validator_session_missing_section(sample_data: dict[str, Any]) -> None:
    """Test session referencing missing section ID fails."""
    invalid_sess = TeachingSession(
        session_id="CS101_T1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="SEC_MISSING",
        subject_code="CS101",
    )
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions([invalid_sess])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent section 'SEC_MISSING'" in str(exc.value)


def test_validator_session_missing_subject(sample_data: dict[str, Any]) -> None:
    """Test session referencing missing subject code fails."""
    invalid_sess = TeachingSession(
        session_id="CS101_T1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS_MISSING",
    )
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions([invalid_sess])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent subject 'CS_MISSING'" in str(exc.value)


def test_validator_session_missing_dependency(sample_data: dict[str, Any]) -> None:
    """Test session referencing non-existent dependency ID fails."""
    # Add a dependency "MISSING_DEP" to session
    sess = TeachingSession(
        session_id="CS101_T1",
        requirement_id="REQ1",
        session_type=SessionType.THEORY,
        duration=1,
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        dependencies=["MISSING_DEP"],
    )
    builder = (
        SchedulingInstanceBuilder()
        .set_faculties(sample_data["faculties"])
        .set_subjects(sample_data["subjects"])
        .set_rooms(sample_data["rooms"])
        .set_sections(sample_data["sections"])
        .set_slots(sample_data["slots"])
        .set_requirements(sample_data["requirements"])
        .set_sessions([sess])
    )
    with pytest.raises(ValidationError) as exc:
        builder.build()
    assert "references non-existent dependency session 'MISSING_DEP'" in str(exc.value)


def test_instance_deserialization_invalid_json() -> None:
    """Test deserialization with invalid JSON throws ValidationError."""
    serializer = InstanceSerializer()
    with pytest.raises(ValidationError) as exc:
        serializer.deserialize("{invalid json")
    assert "Failed to deserialize instance" in str(exc.value)


def test_builder_setters(sample_data: dict[str, Any]) -> None:
    """Test that all builder setter methods return self correctly."""
    builder = SchedulingInstanceBuilder()
    assert builder.set_faculties([]) is builder
    assert builder.set_subjects([]) is builder
    assert builder.set_rooms([]) is builder
    assert builder.set_sections([]) is builder
    assert builder.set_slots([]) is builder
    assert builder.set_holidays([]) is builder
    assert builder.set_requirements([]) is builder
    assert builder.set_sessions([]) is builder
    assert builder.set_config({}) is builder
    assert builder.set_metadata({}) is builder
    assert builder.set_constraint_set(None) is builder
