"""Composite validator and master TimetableValidator implementations."""

import logging
from typing import Any

from brain.models.faculty import Faculty
from brain.models.room import Room
from brain.models.section import Section
from brain.models.slot import Slot
from brain.models.subject import Subject
from brain.models.timetable import Timetable
from brain.validation.base import BaseValidator, ValidationResult, ValidationWarning
from brain.validation.calendar_validator import CalendarValidator
from brain.validation.faculty_validator import FacultyValidator
from brain.validation.room_validator import RoomValidator
from brain.validation.section_validator import SectionValidator
from brain.validation.subject_validator import SubjectValidator

logger = logging.getLogger(__name__)


class CompositeValidator(BaseValidator[Any]):
    """Runs multiple validators sequentially and combines their results."""

    def __init__(self, validators: list[BaseValidator[Any]]) -> None:
        """Initialize with a list of validators.

        Args:
            validators: A list of validator instances.
        """
        self.validators = validators

    def validate(self, data: Any) -> ValidationResult:
        """Run all child validators against the data.

        Args:
            data: The data to validate.

        Returns:
            A combined ValidationResult.
        """
        combined_errors: list[str] = []
        combined_warnings: list[ValidationWarning] = []

        for validator in self.validators:
            try:
                res = validator.validate(data)
                combined_errors.extend(res.errors)
                combined_warnings.extend(res.warnings)
            except Exception as e:
                msg = (
                    f"Unexpected validation error in "
                    f"{validator.__class__.__name__}: {e}"
                )
                logger.error(msg)
                combined_errors.append(msg)

        return ValidationResult(
            is_valid=len(combined_errors) == 0,
            errors=combined_errors,
            warnings=combined_warnings,
        )


class TimetableValidator(BaseValidator[Timetable]):
    """Master validator for a Timetable against the system datasets."""

    def __init__(
        self,
        faculties: list[Faculty],
        rooms: list[Room],
        subjects: list[Subject],
        sections: list[Section],
        slots: list[Slot],
        holidays: list[str] | None = None,
    ) -> None:
        """Initialize with scheduling context datasets.

        Args:
            faculties: List of all faculties.
            rooms: List of all rooms.
            subjects: List of all subjects.
            sections: List of all sections.
            slots: List of all slots.
            holidays: List of slot IDs representing holidays.
        """
        self.faculties = faculties
        self.rooms = rooms
        self.subjects = subjects
        self.sections = sections
        self.slots = slots
        self.holidays = holidays or []

        self.faculty_val = FacultyValidator(all_slots=[s.slot_id for s in slots])
        self.room_val = RoomValidator()
        self.subject_val = SubjectValidator()
        self.calendar_val = CalendarValidator(holidays=self.holidays)
        self.section_val = SectionValidator(sections=sections, rooms=rooms)

    def validate(self, data: Timetable) -> ValidationResult:
        """Validate the complete Timetable and all static context datasets.

        Args:
            data: The Timetable instance.

        Returns:
            A ValidationResult.
        """
        # Validate datasets
        fac_res = self.faculty_val.validate(self.faculties)
        room_res = self.room_val.validate(self.rooms)
        sub_res = self.subject_val.validate(self.subjects)

        # Validate timetable assignments
        cal_res = self.calendar_val.validate(data.assignments)
        sec_res = self.section_val.validate(data.assignments)

        # Combine results
        errors: list[str] = []
        warnings: list[ValidationWarning] = []

        for res in [fac_res, room_res, sub_res, cal_res, sec_res]:
            errors.extend(res.errors)
            warnings.extend(res.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
