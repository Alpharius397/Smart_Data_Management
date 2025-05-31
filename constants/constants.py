import typing
import re

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


class ReportStructure(typing.NamedTuple):
    profile_img: list[str]
    personal_info: list[str]
    sem_data: dict[str, list[str]]

    @staticmethod
    def get_structure(
        columns: list[str], image_columns: list[str]
    ) -> "ReportStructure":
        sem_data = r".+Sem_(\d+)$"

        profile_col = image_columns
        sem_col = [i for i in columns if re.match(sem_data, i)]
        personal_col = [
            i
            for i in columns
            if ((i not in set(profile_col)) and (i not in set(sem_col)))
        ]

        sem_dict: dict[str, list[str]] = {}

        for i in sem_col:
            _sem: list[str] = re.findall(sem_data, i)

            if _sem:
                sem = _sem[0]
                if sem not in sem_dict:
                    sem_dict[sem] = list()
                sem_dict[sem].append(i)

        return ReportStructure(
            profile_img=profile_col, personal_info=personal_col, sem_data=sem_dict
        )
