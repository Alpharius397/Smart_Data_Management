class MainException(Exception):
    """ Base Class Exception for Custom Exception """
    def __init__(self,msg:str) -> None:
        self.msg = msg
        
    def __str__(self) -> str:
        return self.msg
    
    def get_error(self) -> str:
        return str(self)

class NoErrorInForm(MainException):
    def __init__(self):
        super().__init__(f"Form has no error")