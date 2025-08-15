from Main.errors import MainException


class ReadTokenExpired(MainException):
    def __init__(self):
        super().__init__("Read Token has expired! Please try again")


class ReadFailed(MainException):
    def __init__(self) -> None:
        super().__init__("Retrieved Data was of incorrect format")
