from Main.errors import MainException


class ManagerAlreadyAssigned(MainException):
    def __init__(self, manager: int, fileID: int) -> None:
        super().__init__(
            f"Manager with ID: {manager} is already assigned to Task ID: {fileID}"
        )


class ManagerDoesNotExist(MainException):
    def __init__(self, manager: int, fileID: int) -> None:
        super().__init__(
            f"Manager with ID: {manager} was neverr assigned to Task ID: {fileID}"
        )

class ColumnDoesNotExist(MainException):
    def __init__(self, id: int, column: str) -> None:
        super().__init__(
            f"Column '{column}' does not exists in Row ID '{id}'!"
        )


class RowLocked(MainException):
    def __init__(self, id: int) -> None:
        super().__init__(
            f"Row ID '{id}' is locked! Editing is not allowed"
        )

class OnlyTextAllowed(MainException):
    def __init__(self, column: str):
        super().__init__(f"Column '{column}' only accepts text not images!")
        
class OnlyImageAllowed(MainException):
    def __init__(self, column: str):
        super().__init__(f"Column '{column}' only accepts images not text!")