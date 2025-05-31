from Main.errors import MainException


class SubjectsNotDefined(MainException):
    """Exception if Subjects of the Branch are not defined"""

    def __init__(self, branchID: int) -> None:
        super().__init__(
            f"Subjects of the Branch with ID {
                branchID
            } are not defined. Please add the Subjects"
        )
