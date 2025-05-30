from Main.errors import MainException


class ReadTokenExpired(MainException):
    def __init__(self):
        super().__init__("Read Token has expired! Please try agaain")

 t
