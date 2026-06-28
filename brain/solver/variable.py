from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .variable_types import VariableType


class Variable(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    kind: VariableType

    lower_bound: int
    upper_bound: int

    metadata: dict[str, Any] = Field(default_factory=dict)


class AssignmentVariable(Variable):
    lecture_id: str
    faculty_id: str
    room_id: str
    slot_id: str


class RoomVariable(Variable):
    lecture_id: str
    room_id: str


class SlotVariable(Variable):
    lecture_id: str
    slot_id: str


class IntervalVariable(Variable):
    lecture_id: str


class IntegerVariable(Variable):
    pass


class BooleanVariable(Variable):
    pass
