# generic template rn
from collections.abc import Callable
from typing import Any

from .variable import (
    AssignmentVariable,
    IntervalVariable,
    RoomVariable,
    SlotVariable,
)
from .variable_encoder import VariableEncoder
from .variable_registry import VariableRegistry
from .variable_types import VariableType


class VariableBuilder:
    def __init__(
        self,
        constraint_set: Any,
        graph: Any,
        registry: VariableRegistry | None = None,
    ) -> None:
        self.constraint_set = constraint_set
        self.graph = graph
        self._registry = registry or VariableRegistry()

    @property
    def registry(self) -> VariableRegistry:
        return self._registry

    def build_assignment_variables(
        self,
        lectures: Any,
        feasible_rooms: Callable[[Any], Any],
        feasible_slots: Callable[[Any], Any],
    ) -> None:

        for lecture in lectures:
            rooms = feasible_rooms(lecture)

            slots = feasible_slots(lecture)

            for room in rooms:
                for slot in slots:
                    variable = AssignmentVariable(
                        name=VariableEncoder.assignment(
                            lecture.id,
                            room.id,
                            slot.id,
                        ),
                        kind=VariableType.ASSIGNMENT,
                        lower_bound=0,
                        upper_bound=1,
                        lecture_id=lecture.id,
                        faculty_id=lecture.faculty_id,
                        room_id=room.id,
                        slot_id=slot.id,
                        metadata={
                            "lecture_id": lecture.id,
                            "faculty_id": lecture.faculty_id,
                            "room_id": room.id,
                            "slot_id": slot.id,
                            "course_id": lecture.course_id,
                            "semester_id": lecture.semester_id,
                        },
                    )

                    self._registry.register(variable)

    def build_room_variables(
        self,
        lectures: Any,
        feasible_rooms: Callable[[Any], Any],
    ) -> None:

        for lecture in lectures:
            for room in feasible_rooms(lecture):
                variable = RoomVariable(
                    name=VariableEncoder.room(
                        lecture.id,
                        room.id,
                    ),
                    kind=VariableType.ROOM,
                    lower_bound=0,
                    upper_bound=1,
                    lecture_id=lecture.id,
                    room_id=room.id,
                    metadata={
                        "lecture_id": lecture.id,
                        "faculty_id": lecture.faculty_id,
                        "room_id": room.id,
                        "course_id": lecture.course_id,
                        "semester_id": lecture.semester_id,
                    },
                )

                self._registry.register(variable)

    def build_slot_variables(
        self,
        lectures: Any,
        feasible_slots: Callable[[Any], Any],
    ) -> None:

        for lecture in lectures:
            for slot in feasible_slots(lecture):
                variable = SlotVariable(
                    name=VariableEncoder.slot(
                        lecture.id,
                        slot.id,
                    ),
                    kind=VariableType.SLOT,
                    lower_bound=0,
                    upper_bound=1,
                    lecture_id=lecture.id,
                    slot_id=slot.id,
                    metadata={
                        "lecture_id": lecture.id,
                        "faculty_id": lecture.faculty_id,
                        "slot_id": slot.id,
                        "course_id": lecture.course_id,
                        "semester_id": lecture.semester_id,
                    },
                )

                self._registry.register(variable)

    def build_interval_variables(
        self,
        lectures: Any,
    ) -> None:

        for lecture in lectures:
            variable = IntervalVariable(
                name=VariableEncoder.interval(
                    lecture.id,
                ),
                kind=VariableType.INTERVAL,
                lower_bound=0,
                upper_bound=0,
                lecture_id=lecture.id,
                metadata={
                    "lecture_id": lecture.id,
                    "faculty_id": lecture.faculty_id,
                    "course_id": lecture.course_id,
                    "semester_id": lecture.semester_id,
                },
            )

            self._registry.register(variable)
