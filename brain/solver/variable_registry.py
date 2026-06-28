from .exceptions import VariableAlreadyExistsError
from .variable import Variable


class VariableRegistry:

    def __init__(self):
        self._variables: dict[str, Variable] = {}

    def register(self, variable: Variable):

        if variable.name in self._variables:
            raise VariableAlreadyExistsError(
                f"Variable '{variable.name}' already exists."
            )

        self._variables[variable.name] = variable

    def exists(self, name: str) -> bool:
        return name in self._variables

    def get(self, name: str) -> Variable:
        return self._variables[name]

    def clear(self):
        self._variables.clear()

    def count(self) -> int:
        return len(self._variables)

    def all(self):
        return list(self._variables.values())

    def export(self):
        return [
            variable.model_dump(mode="json")
            for variable in self._variables.values()
        ]