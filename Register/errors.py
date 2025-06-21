from Main.errors import MainException

class UserExists(MainException):
    def __init__(self):
        super().__init__("User exists with similar username or email")
        
class InvalidLevel(MainException):
    def __init__(self, level: str):
        super().__init__(f"Level {level} is not present! Please choose a valid option")