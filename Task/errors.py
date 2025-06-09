from Main.errors import MainException

class FileNameExists(MainException):
    def __init__(self):
        super().__init__(f"A File with similar filename already exists! Please change the filename")
        
class TaskDoesNotExists(MainException):
    def __init__(self, task: int):
        super().__init__(f"Task with ID {task} doesn't exists!")
        
class FileLocked(MainException):
    def __init__(self, fileId:int):
        super().__init__(f"File ID {fileId} is Locked and Deletion is not possible!")
        
class InvalidForm(MainException):
    def __init__(self):
        super().__init__("Invalid Form!")
        
class FileProcessFailed(MainException):
    def __init__(self):
        super().__init__("File processing failed. Please Try Again!")

class ManagerAlreadyAssigned(MainException):
    def __init__(self, manager: int, taskID: int) -> None:
        super().__init__(
            f"Manager with ID: {manager} is already assigned to Task ID: {taskID}"
        )

class ManagerNeverAssigned(MainException):
    def __init__(self, manager: int, taskID: int) -> None:
        super().__init__(
            f"Manager with ID: {manager} was never assigned to Task ID: {taskID}"
        )

class ColumnNotFound(MainException):
    def __init__(self, column: str):
        super().__init__(f"Column '{column}' was not found in the option!")