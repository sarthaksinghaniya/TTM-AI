"""Integrity and cross-reference validation for SchedulingInstance."""

from brain.models.exceptions import ValidationError
from brain.problem.scheduling_instance import SchedulingInstance


class InstanceValidator:
    """Validator class ensuring consistency and integrity of a SchedulingInstance."""

    def validate(self, instance: SchedulingInstance) -> None:
        """Validate references, duplicate IDs, and logical boundaries in the instance.

        Args:
            instance: The SchedulingInstance to validate.

        Raises:
            ValidationError: If any validation rule is violated.
        """
        # 1. Check duplicate IDs
        self._check_duplicates([f.faculty_id for f in instance.faculties], "faculty")
        self._check_duplicates([s.subject_code for s in instance.subjects], "subject")
        self._check_duplicates([r.room_id for r in instance.rooms], "room")
        self._check_duplicates([sec.section_id for sec in instance.sections], "section")
        self._check_duplicates([s.slot_id for s in instance.slots], "slot")
        self._check_duplicates(
            [req.requirement_id for req in instance.requirements],
            "teaching_requirement",
        )
        self._check_duplicates(
            [sess.session_id for sess in instance.sessions], "teaching_session"
        )

        # Build reference lookup sets
        faculty_ids = {f.faculty_id for f in instance.faculties}
        subject_codes = {s.subject_code for s in instance.subjects}
        section_ids = {sec.section_id for sec in instance.sections}
        requirement_ids = {req.requirement_id for req in instance.requirements}
        session_ids = {sess.session_id for sess in instance.sessions}

        # 2. Validate TeachingRequirements references
        for req in instance.requirements:
            if req.faculty_id not in faculty_ids:
                raise ValidationError(
                    "faculty_id",
                    f"TeachingRequirement '{req.requirement_id}' references "
                    f"non-existent faculty '{req.faculty_id}'",
                )
            if req.section_id not in section_ids:
                raise ValidationError(
                    "section_id",
                    f"TeachingRequirement '{req.requirement_id}' references "
                    f"non-existent section '{req.section_id}'",
                )
            if req.subject_code not in subject_codes:
                raise ValidationError(
                    "subject_code",
                    f"TeachingRequirement '{req.requirement_id}' references "
                    f"non-existent subject '{req.subject_code}'",
                )

        # 3. Validate TeachingSessions references and dependencies
        for sess in instance.sessions:
            if sess.requirement_id not in requirement_ids:
                raise ValidationError(
                    "requirement_id",
                    f"TeachingSession '{sess.session_id}' references "
                    f"non-existent requirement '{sess.requirement_id}'",
                )
            if sess.faculty_id not in faculty_ids:
                raise ValidationError(
                    "faculty_id",
                    f"TeachingSession '{sess.session_id}' references "
                    f"non-existent faculty '{sess.faculty_id}'",
                )
            if sess.section_id not in section_ids:
                raise ValidationError(
                    "section_id",
                    f"TeachingSession '{sess.session_id}' references "
                    f"non-existent section '{sess.section_id}'",
                )
            if sess.subject_code not in subject_codes:
                raise ValidationError(
                    "subject_code",
                    f"TeachingSession '{sess.session_id}' references "
                    f"non-existent subject '{sess.subject_code}'",
                )

            # Check dependencies exist within the session set
            for dep in sess.dependencies:
                if dep not in session_ids:
                    raise ValidationError(
                        "dependency",
                        f"TeachingSession '{sess.session_id}' references "
                        f"non-existent dependency session '{dep}'",
                    )

    def _check_duplicates(self, ids: list[str], entity_name: str) -> None:
        """Helper to identify duplicate IDs in lists.

        Args:
            ids: List of string identifiers.
            entity_name: Name of the entity being validated.

        Raises:
            ValidationError: If duplicate IDs are found.
        """
        seen = set()
        for item_id in ids:
            if item_id in seen:
                raise ValidationError(
                    entity_name,
                    f"Duplicate identifier '{item_id}' found in {entity_name} list",
                )
            seen.add(item_id)
        # Empty arrays are fine, we just check uniqueness.
