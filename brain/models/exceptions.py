"""Custom exceptions for HanuPlanner Brain scheduler."""


class ValidationError(Exception):
    """Exception raised for validation errors.

    Attributes:
        args: Positional arguments containing details of the validation error.
    """

    def __init__(self, *args: object) -> None:
        """Initialize the ValidationError with flexible arguments."""
        super().__init__(*args)


class ConstraintError(Exception):
    """Exception raised for constraint violations or configuration errors.

    Attributes:
        args: Positional arguments containing details of the constraint error.
    """

    def __init__(self, *args: object) -> None:
        """Initialize the ConstraintError with flexible arguments."""
        super().__init__(*args)


class GraphBuildError(Exception):
    """Exception raised when building the conflict graph fails.

    Attributes:
        args: Positional arguments containing details of the graph build error.
    """

    def __init__(self, *args: object) -> None:
        """Initialize the GraphBuildError with flexible arguments."""
        super().__init__(*args)


class SchedulingError(Exception):
    """Exception raised when scheduling fails.

    Attributes:
        args: Positional arguments containing details of the scheduling error.
    """

    def __init__(self, *args: object) -> None:
        """Initialize the SchedulingError with flexible arguments."""
        super().__init__(*args)
