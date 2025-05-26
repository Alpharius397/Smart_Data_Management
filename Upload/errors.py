from Main.errors import MainException

class FileNameExists(MainException):
    def __init__(self):
        super().__init__(f"A File with similar filename already exists! Please change the filename")
        
class FileDoesNotExists(MainException):
    def __init__(self, fileID: int):
        super().__init__(f"File with ID {fileID} doesn't exists!")
        
class FileLocked(MainException):
    def __init__(self, fileId:int):
        super().__init__(f"File ID {fileId} is Locked and Deletion is not possible!")
        
class InvalidForm(MainException):
    def __init__(self):
        super().__init__("Invalid Form!")
        
class FileProcessFailed(MainException):
    def __init__(self):
        super().__init__("File processing failed. Please Try Again!")