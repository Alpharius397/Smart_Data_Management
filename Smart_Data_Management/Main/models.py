import pymongo
import pymongo.collection
import pymongo.client_session
from typing import NamedTuple
from django.conf import settings
from Logs.loggers import MONGO_LOG, REDIS_LOG
import redis

class MongoTemplate:
    """
        Data Structure:
        {
            header:{
                post:{
                    university, 
                    institute, 
                    branch
                }
                uploader,
                manager
            }
            data:{
                excel,   
                header:{
                    image_column,
                    file_name,
                },
                feed:[
                    {
                        locked,
                        time_of_issue,
                        status,
                        feed,
                    },
                ]
            }
        }
    """
    def __init__(self) -> None:
        
        self.header:dict[str,dict[str,str]|list] = {'post':{'university':None,'institute':None,'branch':None},'uploader':None,'manager':[]}
        self.data_header:dict[str,str|list] = {'file_name':None,'image_column':[]}
        self.data_feed:dict[str,str] = {'locked':None,'time_of_lock':None,'status':None,'feed':None,'time_of_issue':None,'issued':None}
        self.data = None
        self.feed:dict[str,dict[str,str]] = {}
        
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
        self.feed = [{"index":i,**self.data_feed} for i in range(rows)]
        return self
    
    def add_manager(self, managers:list[str]) -> 'MongoTemplate':
        for i in managers:
            self.header['manager'].append(i)
        return self
    
    def get_json(self) -> dict:
        return {'header':self.header,'data':{'excel':self.data,'header':self.data_header,'feed':self.feed}}
    
class MongoDB(NamedTuple):
    database:str
    collection:str
    
class MongoConnection:
    
    log = MONGO_LOG
    
    def __init__(self) -> None:
        self.connection = pymongo.MongoClient(settings.MONGO_URL)
        self.collection:pymongo.collection.Collection = None
    
    def is_connected(self) -> bool:
        return (self.collection is not None)
    
    
    def connect(self) -> 'MongoConnection':

        try:
            self.connection.server_info()
            self.collection = self.connection.get_database(settings.MONGO_CRED.database).get_collection(settings.MONGO_CRED.collection)            
            data_url=', '.join([f"mongodb://{host}:{port}/" for host,port in self.connection.nodes])
            self.log.write_info(f"Established Connection to {data_url}")
            
        except Exception as e:            
            self.log.write_error(msg = self.log.get_error_info(e))
            
        return self
    
    def find_one(self, condition:dict, filters:dict = {}) -> dict:
        res:dict = None
        
        try:
            res = self.collection.find_one(condition,filters)
            self.log.write_info(f"Applying search with filters '{condition}' and displaying '{filters}'")
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
        
        return res
    
    def find_all(self, condition:dict, filters:dict = {}) -> dict:
        res:dict = None
        
        try:
            res = self.collection.find(condition,filters)
            self.log.write_info(f"Applying search with filters '{condition}' and displaying '{filters}'")
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
        
        return res
    
    def update_one(self, condition:dict, update:dict) -> bool:
        success:bool = False
        
        try:
            _ = self.collection.update_one(condition,update)
            
            success = bool(_.matched_count==1)
            self.log.write_info(f"Applying updation '{update}' to document '{condition}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return success
    
    
    def delete_one(self, condition:dict) -> bool:
        success:bool = False
        
        try:
            _ = self.collection.delete_one(condition)
            
            success = bool(_.deleted_count==1)
            self.log.write_info(f"Applying deletion to document '{condition}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return success
    
    def insert_one(self, doc:MongoTemplate) -> str:
        
        id:str = None
        try:
            _ = self.collection.insert_one(doc.get_json())
            id = _.inserted_id
            self.log.write_info(f"Inserting document with id '{id}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return id
    
    def replace_one(self, condition:dict, doc: MongoTemplate) -> bool:
        success:bool = False
        
        try:
            _ = self.collection.replace_one(condition,doc.get_json())
            success = bool(_.matched_count==1)
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return success
    
    def close(self):
        try:
            self.connection.close()
            self.log.write_info("Closing MongoDB connection")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
class RedisConnection:
    
    MAX_DURATION:int = 3
    log = REDIS_LOG
    
    def __init__(self):
        self.r = None
        
    def connect(self) -> 'RedisConnection':
        try:
            self.r = redis.Redis(**settings.REDIS,decode_responses=True)
            self.log.write_info("Connecting to Redis Database")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return self
    
    def get(self, key:str) -> str | None:
        
        try:
            value = self.r.get(key)
            self.log.write_info(f"Fetching Key: {key}")
            return value
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return None
    
    def set(self, key:str, value:str, duration:int = None) -> None:
        
        duration = RedisConnection.MAX_DURATION if(duration is None) else duration
        try:
            self.r.set(key, value, ex=RedisConnection.get_secs_from_minutes(duration))
            self.log.write_info(f"Setting Key: {key}, with Value: {value} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
    def unset(self, key: str):
        
        try:
            self.r.unlink(key)
            self.log.write_info(f"Unsetting Key: {key}")      
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
    def close(self):
        try:
            self.r.close()
            self.log.write_info("Closing Redis connection")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
    @staticmethod        
    def get_secs_from_minutes(minutes:int) -> int: 
        return minutes*60