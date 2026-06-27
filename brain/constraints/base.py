"""Base classes and context definitions for scheduling constraints."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from brain.models.conflict import Conflict
from brain.models.constraint import Constraint
from brain.models.faculty import Faculty
from brain.models.room import Room
from brain.models.section import Section
from brain.models.slot import Slot
from brain.models.subject import Subject
from brain.models.timetable import Timetable


class ConstraintContext(BaseModel):
    """Context dataset required for constraint evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    faculties: list[Faculty] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    subjects: list[Subject] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    slots: list[Slot] = Field(default_factory=list)
    holidays: list[str] = Field(default_factory=list)


class BaseConstraintEvaluator(ABC):
    """Abstract base class for all constraint evaluators."""

    def __init__(self, definition: Constraint) -> None:
        """Initialize the evaluator with its Constraint model definition.

        Args:
            definition: The Constraint model configuration.
        """
        self.definition = definition

    @abstractmethod
    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate the timetable against this constraint.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        pass
