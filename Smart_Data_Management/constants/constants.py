import typing
import re

MAX_RECORD:int = 5
LOADING:str = "Loading"
DONE:str = "Done"
NONE:str = "None"
FAILED:str = "Failed"
WRITE_TOKEN:str = "write-token"
ERROR_JSON:dict[str, str|bool] = {"info":"Unauthenticated Request","status":False}
VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}
READ_TOKEN:str = "read-token"
LOADING:str = "Loading"
CARD_DATA:str = "Data"
DEFAULT_ERROR:str = "Something Went Wrong! Please try Again"
MONGO_ERROR:str = "MongoDB Connection Failed"

class ReportStructure(typing.NamedTuple):
    profile_img:str
    personal_info:list[str]
    sem_data:dict[str,list[str]]

    @staticmethod
    def get_structure(columns: list[str]) -> 'ReportStructure':
        
        profile_img = r'^Profile_Image$'
        sem_data = r'.+Sem_(\d+)$'
        
        _profile_col = [i for i in columns if re.match(profile_img,i)]
        sem_col = [i for i in columns if re.match(sem_data,i)]
        personal_col = [i for i in columns if((i not in set(_profile_col)) and (i not in set(sem_col)))]
        
        sem_dict:dict[str,list[str]] = {}
        
        profile_col = _profile_col[0] if _profile_col else ''
        
        for i in sem_col:
            _sem:list[str] = re.findall(sem_data,i)
            
            if(_sem):
                sem = _sem[0]
                if(sem not in sem_dict): sem_dict[sem] = list()
                sem_dict[sem].append(i)
                
        return ReportStructure(profile_img=profile_col, personal_info=personal_col, sem_data=sem_dict)