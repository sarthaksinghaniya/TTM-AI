from enum import Enum


class VariableType(str, Enum):
    ASSIGNMENT = "assignment"
    ROOM = "room"
    SLOT = "slot"
    INTERVAL = "interval"
    INTEGER = "integer"
    BOOLEAN = "boolean"