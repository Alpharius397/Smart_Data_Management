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
