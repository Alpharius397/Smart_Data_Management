from Main.errors import MainException


class UserNameAlreadyExists(MainException):
    def __init__(self, username: str):
        super().__init__(f"Username {username} already exists")


class EmailAlreadyExists(MainException):
    def __init__(self, email: str):
        super().__init__(f"Email {email} is already registered to another user")


class PasswordMismatch(MainException):
    def __init__(self) -> None:
        super().__init__("Previous Password is incorrect! Please try again")

class OTPWrong(MainException):
    def __init__(self) -> None:
        super().__init__("Provided OTP is incorrect! Please try again")