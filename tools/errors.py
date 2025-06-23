from Main.errors import MainException


class ImageCompressionFailed(MainException):
    def __init__(self) -> None:
        super().__init__("Image Compression Failed")


class ImageExpansionFailed(MainException):
    def __init__(self) -> None:
        super().__init__("Image Expansion Failed")


class IncorrectDataFormat(MainException):
    def __init__(self) -> None:
        super().__init__("Incorrect Data Format detected")

class TokenExpired(MainException):
    def __init__(self):
        super().__init__("Token has expired! Please try again")