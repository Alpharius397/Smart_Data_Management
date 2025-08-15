import typing
import re

OTP_SIZE: int = 6
MAX_RECORD: int = 5
LOADING: str = "Loading"
DONE: str = "Done"
NONE: str = "None"
FAILED: str = "Failed"
WRITE_TOKEN: str = "write-token"
ERROR_JSON: dict[str, str | bool] = {"info": "Unauthenticated Request", "status": False}
VIEW_DATA = {"_id": 1, "header": 1, "data.header.file_name": 1}
READ_TOKEN: str = "read-token"
CARD_DATA: str = "Data"
DEFAULT_ERROR: str = "Something Went Wrong! Please try Again"
MONGO_ERROR: str = "MongoDB Connection Failed"
WRONG_IMAGE: str = "Incorrect Image Format Detected"
WRONG_PERSONAL: str = "Incorrect Data Format Detected"
WRONG_SEM: str = "Incorrect Semester Format Detected"
SUCCESS: str = "success"
ERROR: str = "error"
WARNING: str = "warning"
OTP_SUBJECT = "OTP Required to Confirm Your {0} Change"
""" use .format to add custom change header """
OTP_MESSAGE = "Your OTP for {0} Change is {1}"
""" use .format to add custom change header """
OTP_KEY = "OTP"
EMAIL_KEY = "EMAIL"
ACCESS_PDF = "Access-PDF"
ACCESS_TOKEN = "Access-Token"

SUCCESS_SUBJECT = "Request for {0} change"
SUCCESS_MESSAGE = "{0} change was successfully changed"

DELETE_SUBJECT = "Account Deleteion Request"
DELETE_MESSAGE = "Account with username {0} deleted successfully"