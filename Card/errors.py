from Main.errors import MainException


class CardIdMissing(MainException):
    def __init__(self):
        super().__init__("Card ID is missing")
