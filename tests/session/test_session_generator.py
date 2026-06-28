"""Tests for HanuPlanner Brain curriculum session generator."""

import time

import pytest
from pydantic import ValidationError as PydanticValidationError

from brain.models import TeachingRequirement, ValidationError
from brain.session import (
    SessionFactory,
    SessionGenerator,
    SessionType,
    TeachingSession,
)


def test_generator_empty_list() -> None:
    """Test generating sessions from empty requirements list."""
    gen = SessionGenerator()
    sessions, stats = gen.generate_sessions([])
    assert len(sessions) == 0
    assert stats.total_requirements_processed == 0
    assert stats.total_sessions_generated == 0
    assert stats.total_duration_hours == 0


def test_generator_invalid_max_theory_duration() -> None:
    """Test that max_theory_duration < 1 raises ValidationError."""
    gen = SessionGenerator()
    with pytest.raises(ValidationError):
        gen.generate_sessions([], max_theory_duration=0)


def test_generator_simple_theory() -> None:
    """Test generating a simple theory session."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    session = sessions[0]
    assert session.session_id == "CS101_T1"
    assert session.session_type == SessionType.THEORY
    assert session.duration == 1
    assert session.faculty_id == "F1"
    assert stats.theory_sessions_count == 1
    assert stats.lab_sessions_count == 0


def test_generator_simple_lab() -> None:
    """Test generating a simple lab session."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=0,
        weekly_lab_hours=2,
        preferred_room_type="LAB",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    session = sessions[0]
    assert session.session_id == "CS101_L1"
    assert session.session_type == SessionType.LAB
    assert session.duration == 2
    assert stats.theory_sessions_count == 0
    assert stats.lab_sessions_count == 1


def test_generator_theory_split_default() -> None:
    """Test splitting theory hours with default max duration of 1."""
    gen = SessionGenerator()
    req = TeachingRequirement(
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
    sessions, _stats = gen.generate_sessions([req], max_theory_duration=1)
    assert len(sessions) == 3
    assert [s.duration for s in sessions] == [1, 1, 1]
    assert [s.session_id for s in sessions] == [
        "CS101_T1",
        "CS101_T2",
        "CS101_T3",
    ]


def test_generator_theory_split_custom() -> None:
    """Test splitting theory hours with custom max duration of 2."""
    gen = SessionGenerator()
    req = TeachingRequirement(
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
    sessions, _stats = gen.generate_sessions([req], max_theory_duration=2)
    assert len(sessions) == 2
    assert [s.duration for s in sessions] == [2, 1]
    assert [s.session_id for s in sessions] == ["CS101_T1", "CS101_T2"]


def test_generator_theory_split_custom_exact() -> None:
    """Test splitting theory hours where hours is a multiple of max duration."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=4,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req], max_theory_duration=2)
    assert len(sessions) == 2
    assert [s.duration for s in sessions] == [2, 2]


def test_generator_theory_split_custom_large() -> None:
    """Test splitting theory hours where hours requires multiple splits."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=5,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req], max_theory_duration=2)
    assert len(sessions) == 3
    assert [s.duration for s in sessions] == [2, 2, 1]


def test_generator_continuous_lab() -> None:
    """Test that lab session is generated continuous."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=0,
        weekly_lab_hours=3,
        preferred_room_type="LAB",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    assert sessions[0].duration == 3


def test_generator_linked_lab_to_theory_true() -> None:
    """Test linking lab session dependency to first theory session."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="LAB",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req], link_lab_to_theory=True)
    # 2 theory sessions (T1, T2) + 1 lab session (L1) = 3 sessions
    assert len(sessions) == 3
    lab_sess = next(s for s in sessions if s.session_type == SessionType.LAB)
    assert lab_sess.dependencies == ["CS101_T1"]


def test_generator_linked_lab_to_theory_false() -> None:
    """Test when link_lab_to_theory is False dependency list remains empty."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="LAB",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req], link_lab_to_theory=False)
    assert len(sessions) == 3
    lab_sess = next(s for s in sessions if s.session_type == SessionType.LAB)
    assert lab_sess.dependencies == []


def test_generator_linked_lab_without_theory() -> None:
    """Test linking lab session when there are no theory hours."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=0,
        weekly_lab_hours=2,
        preferred_room_type="LAB",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req], link_lab_to_theory=True)
    assert len(sessions) == 1
    assert sessions[0].dependencies == []


def test_generator_tutorial_via_room_type() -> None:
    """Test tutorial session generation based on room type constraint."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="TUTORIAL",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    assert sessions[0].session_type == SessionType.TUTORIAL
    assert stats.tutorial_sessions_count == 1
    assert stats.theory_sessions_count == 0


def test_generator_tutorial_via_room_type_case_insensitive() -> None:
    """Test case insensitivity on preferred_room_type tutorial check."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="tutorial",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    assert sessions[0].session_type == SessionType.TUTORIAL


def test_generator_tutorial_via_constraint_ref() -> None:
    """Test tutorial session generation based on constraint_refs."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=["Tutorial"],
    )
    sessions, _stats = gen.generate_sessions([req])
    assert len(sessions) == 1
    assert sessions[0].session_type == SessionType.TUTORIAL


def test_generator_priority_assignment() -> None:
    """Test priority heuristic assignment defaults to 1."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req])
    assert sessions[0].priority == 1


def test_generator_fixed_field_false() -> None:
    """Test fixed field default is False."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="REQ1",
        faculty_id="F1",
        section_id="SEC1",
        subject_code="CS101",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="Batch A",
        constraint_refs=[],
    )
    sessions, _stats = gen.generate_sessions([req])
    assert sessions[0].fixed is False


def test_generator_statistics_processed_requirements() -> None:
    """Test statistics tracking for processed requirements count."""
    gen = SessionGenerator()
    req1 = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    req2 = TeachingRequirement(
        requirement_id="R2",
        faculty_id="F1",
        section_id="S1",
        subject_code="S2",
        weekly_theory_hours=2,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req1, req2])
    assert stats.total_requirements_processed == 2


def test_generator_statistics_generated_sessions() -> None:
    """Test statistics tracking for total generated sessions count."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req], max_theory_duration=1)
    # T1 + T2 + L1 = 3 sessions
    assert stats.total_sessions_generated == 3


def test_generator_statistics_theory_sessions_count() -> None:
    """Test statistics tracking for theory sessions count."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req])
    assert stats.theory_sessions_count == 2


def test_generator_statistics_lab_sessions_count() -> None:
    """Test statistics tracking for lab sessions count."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req])
    assert stats.lab_sessions_count == 1


def test_generator_statistics_tutorial_sessions_count() -> None:
    """Test statistics tracking for tutorial sessions count."""
    gen = SessionGenerator()
    req = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=2,
        weekly_lab_hours=2,
        preferred_room_type="TUTORIAL",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req])
    assert stats.tutorial_sessions_count == 2


def test_generator_statistics_total_duration_hours() -> None:
    """Test statistics tracking for total duration sum in hours."""
    gen = SessionGenerator()
    req1 = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="S1",
        weekly_theory_hours=3,
        weekly_lab_hours=2,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    _sessions, stats = gen.generate_sessions([req1])
    assert stats.total_duration_hours == 5


def test_generator_large_dataset_performance() -> None:
    """Verify performance metrics scale linearly O(N) on a large dataset."""
    gen = SessionGenerator()
    large_reqs = [
        TeachingRequirement(
            requirement_id=f"R{i}",
            faculty_id="F1",
            section_id="S1",
            subject_code="S1",
            weekly_theory_hours=3,
            weekly_lab_hours=2,
            preferred_room_type="THEORY",
            batch="B",
            constraint_refs=[],
        )
        for i in range(1000)
    ]
    start = time.perf_counter()
    sessions, _stats = gen.generate_sessions(large_reqs)
    end = time.perf_counter()
    assert len(sessions) == 4000
    assert (end - start) < 0.5  # Linear O(N) mapping should take well under 500ms


def test_session_factory_create_session() -> None:
    """Test SessionFactory creation of TeachingSession instances."""
    req = TeachingRequirement(
        requirement_id="R1",
        faculty_id="F1",
        section_id="S1",
        subject_code="DBMS",
        weekly_theory_hours=1,
        weekly_lab_hours=0,
        preferred_room_type="THEORY",
        batch="B",
        constraint_refs=[],
    )
    session = SessionFactory.create_session(
        requirement=req,
        suffix="T1",
        session_type=SessionType.THEORY,
        duration=2,
        priority=3,
        dependencies=["DBMS_T0"],
    )
    assert session.session_id == "DBMS_T1"
    assert session.session_type == SessionType.THEORY
    assert session.duration == 2
    assert session.priority == 3
    assert session.dependencies == ["DBMS_T0"]


def test_teaching_session_validation_empty_id() -> None:
    """Test TeachingSession ID validation checks."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingSession(
            session_id="  ",
            requirement_id="REQ1",
            session_type=SessionType.THEORY,
            duration=1,
            faculty_id="F1",
            section_id="SEC1",
            subject_code="CS101",
        )


def test_teaching_session_validation_zero_duration() -> None:
    """Test TeachingSession zero duration validation constraint."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingSession(
            session_id="S1",
            requirement_id="REQ1",
            session_type=SessionType.THEORY,
            duration=0,
            faculty_id="F1",
            section_id="SEC1",
            subject_code="CS101",
        )


def test_teaching_session_validation_zero_priority() -> None:
    """Test TeachingSession zero priority validation constraint."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingSession(
            session_id="S1",
            requirement_id="REQ1",
            session_type=SessionType.THEORY,
            duration=1,
            faculty_id="F1",
            section_id="SEC1",
            subject_code="CS101",
            priority=0,
        )


def test_teaching_session_validation_empty_dependency() -> None:
    """Test TeachingSession empty dependency string constraint."""
    with pytest.raises((ValidationError, PydanticValidationError)):
        TeachingSession(
            session_id="S1",
            requirement_id="REQ1",
            session_type=SessionType.THEORY,
            duration=1,
            faculty_id="F1",
            section_id="SEC1",
            subject_code="CS101",
            dependencies=["DBMS_T1", "  "],
        )
