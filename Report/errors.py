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

class InvalidSchema(MainException):
    def __init__(self) -> None:
        super().__init__(
            "Schema Parameter was not found! Please ensure that a valid schema is defined"
        )
        
class DataNotLocked(MainException):
    def __init__(self):
        super().__init__("Current Data is not locked! Please lock the data first")
        
class RedisFailed(MainException):
    def __init__(self):
        super().__init__("Failed To Process Request")