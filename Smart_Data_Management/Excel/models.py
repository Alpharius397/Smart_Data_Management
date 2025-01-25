import pymongo
from typing import NamedTuple
import pymongo.client_session
import pymongo.collection


class MongoDB(NamedTuple):
    database:str
    collection:str

def get_error_info(exception:Exception) -> str:
    if(isinstance(exception,Exception)):
        return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception}"
    
    return "Not an Exception"
    
class MongoConnection:
    connection:pymongo.MongoClient = None
    
    def __init__(self, connect_url:str) -> None:
        self.connection = pymongo.MongoClient(connect_url)
    
    def connect(self, info:MongoDB) -> pymongo.collection.Collection | None:

        result:pymongo.collection.Collection = None

        try:
            self.connection.server_info()
            result = self.connection.get_database(info.database).get_collection(info.collection)
        except Exception as e:            
            print(get_error_info(e))
            
        return result

class MongoTemplate:
    """
        Data Structure:
        
        {
            header:{
                post:{
                    university, institute, branch
                }
                
                uploader,
                manager
            }
            
            data:{
                excel
                
                header:{
                    image_column,
                    file_name
                }
                
                feed:[
                    {
                        locked,
                        time_of_issue,
                        status,
                        feed
                    }
                ]
            }
        }
    
    """
    
    def __init__(self) -> None:
        
        self.header = {'post':{'university':None,'institute':None,'branch':None},'uploader':None,'manager':[]}
        self.data_header = {'file_name':None,'image_column':[]}
        self.data_feed = {'locked':None,'time_of_issue':None,'status':None,'feed':None}
        self.data = None
        self.feed:list[dict] = []
        
        self.template = {'header':self.header,'data':{'excel':self.data,'header':self.data_header,'feed':self.feed}}

    def add_post(self, university:str,institute:str, branch:str) -> 'MongoTemplate':
        self.header['post'] = {'university':university,'institute':institute,'branch':branch}
        return self
    
    def add_uploader(self, uploader:str) -> 'MongoTemplate':
        self.header['uploader'] = uploader
        return self
    
    def add_file(self, file_name:str) -> 'MongoTemplate':
        self.data_header['file_name'] = file_name
        return self
        
    def add_image(self, image_col:list[str]) -> 'MongoTemplate':
        self.data_header['image_column'] = image_col
        return self
    
    def add_excel(self, excel:dict) -> 'MongoTemplate':
        self.data = excel
        return self
    
    def add_feed(self, rows:int) -> 'MongoTemplate':
        for _ in range(rows):
            self.feed.append(self.data_feed)
        return self
    
    def add_manager(self, managers:list[str]) -> 'MongoTemplate':
        for i in managers:
            self.header['manager'].append(i)
        return self
    
    def get_json(self) -> dict:
        return {'header':self.header,'data':{'excel':self.data,'header':self.data_header,'feed':self.feed}}
