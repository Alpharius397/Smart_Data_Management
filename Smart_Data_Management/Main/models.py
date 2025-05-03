from copy import copy
import pandas as pd
import pymongo
import pymongo.collection
from typing import NamedTuple
from django.conf import settings
from Logs.loggers import MONGO_LOG, REDIS_LOG
import redis
import json
from bson  import ObjectId
import typing

class MongoFindQuery(typing.NamedTuple):
    filters:dict[str, str]
    conditions:dict[str, str]
    
    def __iter__(self):
        yield self.conditions
        yield self.filters

class MongoUpdateQuery(typing.NamedTuple):
    where:dict[str, str]
    updates:dict[str, str]

    def __iter__(self):
        yield self.where
        yield self.updates

class MongoDeleteQuery(typing.NamedTuple):
    filters:dict[str, str]
    updates:dict[str, str]
    
    def __iter__(self):
        yield self.filters
        yield self.updates

class MergeQuery(typing.NamedTuple):
    first: dict[str, str] = {}
    second: dict[str, str] = {}

    def __iter__(self):
        yield self.first
        yield self.second

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
                excel:[
                    {
                        row,
                        feed:{
                            locked,
                            time_of_issue,
                            status,
                            feed,   
                            index
                        }
                    }
                ],
                header:{
                    columns,
                    image_column,
                    file_name
                },
                }
            }
        }
    """
    def __init__(self) -> None:
        
        self.header:dict[str,dict[str,str]|list] = {'post':{'university':None,'institute':None,'branch':None},'uploader':None,'manager':[]}
        self.data_header:dict[str,str|list] = {'file_name':None,'image_column':[],'columns':[]}
        self.data_feed:dict[str,str] = {'locked':None,'time_of_lock':None,'status':None,'feed':None,'time_of_issue':None,'issued':None}
        self.data = {}
        self.feed:dict[str,dict[str,str]] = {}
    
    def __generate_feed_idx(self, idx:int) -> dict[str, str]:
        temp = copy(self.data_feed)
        temp.update({'index':idx})
        return temp
        
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
    
    def add_excel(self, excel:pd.DataFrame) -> 'MongoTemplate':

        self.data = [{'row':list(i[1:]), 'feed':self.__generate_feed_idx(i[0])} for i in excel.itertuples()]

        self.data_header['columns'] = list(excel.columns)
        
        return self
    
    def add_manager(self, managers:list[str]) -> 'MongoTemplate':
        self.header['manager'] = list(managers)
        return self
    
    def get_json(self) -> dict:
        return {'header':self.header,'data':{'excel':self.data,'header':self.data_header}}
    
    @staticmethod
    def _buffer_find_query_factory(column_name:str, start:int, limit:int) -> MongoFindQuery:
        conditions:dict[str, str] = {}
        filters:dict[str, str] = {}
        
        if(limit is None):
            filters.update({column_name:{"$slice":[start]}})
            
        else:
            filters.update({column_name:{"$slice":[start, limit]}})

        return MongoFindQuery(filters, conditions)

    @staticmethod
    def _full_find_query_factory(column_name:str) -> MongoFindQuery:
        conditions:dict[str, str] = {}
        filters:dict[str, str] = {}
        
        filters.update({column_name:1})
        
        return MongoFindQuery(filters, conditions)
    
    @staticmethod
    def _single_update_query(column_name:str, value:str|dict|list) -> MongoUpdateQuery:
        where:dict[str, str] = {}
        updates:dict[str, str] = {}
        
        where.update({column_name:{"$exists":True}})
        updates.update({column_name:{"$set":value}})
        
        return MongoUpdateQuery(where=where, updates=updates)

    @staticmethod
    def get_header_query(conditions:dict = {}) -> MongoFindQuery:
        res = MongoTemplate._full_find_query_factory("header")
        res.conditions.update(conditions)
        return res
    
    @staticmethod
    def get_file_name_query(conditions:dict = {}) -> MongoFindQuery:
        res = MongoTemplate._full_find_query_factory("data.header.file_name")
        res.conditions.update(conditions)
        return res

    @staticmethod
    def get_feedback_query(conditions:dict = {}, start:int = 0, limit:int = None) -> MongoFindQuery:
        res = MongoTemplate._buffer_find_query_factory("data.excel.feed", start, limit)
        res.conditions.update(conditions)
        return res

    @staticmethod
    def get_buffer_query(conditions:dict = {}, start:int = 0, limit:int = None) -> MongoFindQuery:
        data_part =  MongoTemplate._buffer_find_query_factory("data.excel", start, limit)
        column_part =  MongoTemplate._full_find_query_factory("data.header")
        
        return MongoTemplate.merge_everything(data_part, column_part, initial_a=conditions)
    
    # db.excel.aggregate([{$match:{_id:ObjectId('6814c195eed58efa05158976')}},{$project:{"data.excel":{$filter:{input:"$data.excel",as:"i", cond:{$eq:[{$arrayElemAt:["$$i", 0]},"z"]}}}}}])
    # db.excel.aggregate([{$project:{arrays:{$filter:{input:"$data.excel",}}}},{$project:{options:{$map:{input:"$$arrays",as:"i", in:{$arrayElemAt:["$$i",0]}}}}},{$project:{final:{$filter:{input:"$options",as:"j",cond:{$regexMatch:{input:"$$j",regex:/[0-9]+/}}}}}}])
    
    @staticmethod
    def get_search_buffer(column_index:int, mongoID:str, value:str, start:int, limit:int) -> list[dict]:
        
        match_pipeline = {"$match":{"_id":ObjectId(mongoID)}}
        search_pipeline = {
                            '$project':{
                                "data.excel":{
                                    '$filter':{
                                        'input':"$data.excel",
                                        'as':"i",
                                        'cond':{
                                            '$regexMatch':{
                                                'input':{
                                                    '$arrayElemAt':["$$i",column_index]
                                                    },
                                                'regex':f'/{value}/i'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
        
        slice_pipeline = {
                            '$project':{
                                "data.excel":{
                                    '$slice':["$data.excel", start, limit]
                                },
                                "header":1,
                                "data.header":1
                            }
                        }
        
        return [match_pipeline,search_pipeline,slice_pipeline]
    
            
    @staticmethod
    def merge_everything(*query:MongoFindQuery|MongoDeleteQuery|MongoUpdateQuery, initial_a:dict = {}, initial_b:dict = {}) -> dict[str, str]:
        
        res = MergeQuery(initial_a, initial_b)
        
        for a,b in query:
            res.first.update(a)
            res.second.update(b)
            
        return res

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
    
    def find_all(self, condition:dict, filters:dict = {}) -> list[dict]:
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
            self.log.write_info(f"Replacing document with filters '{condition}'")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return success
    
    def close(self):
        try:
            self.connection.close()
            self.log.write_info("Closing MongoDB connection")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
    
    def aggregate(self, match_pipeline:dict[str,str|dict], search_pipeline:dict[str,str|dict]) -> list[dict[str, str]]:
        result:list[dict[str, str]] = []
        try: 
            result = self.collection.aggregate([match_pipeline, search_pipeline])
            self.log.write_info(f"Aggregating pipeline with [{match_pipeline},{search_pipeline}]")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return result
    
    @staticmethod
    def getValue(dictionary: dict, default:dict|list|str|int, *keyString:str|int) -> str | int | dict | list:
        
        def get_default(value: dict|list, key:str|int):
            try:
                if(isinstance(value,dict)):
                    return value.get(key, None)
                elif(isinstance(value, list) and isinstance(key, int)):
                    return value.__getitem__(int(key))
                else:
                    return value
            except Exception as e:
                return default()
        
        val = dictionary
        
        for key in keyString:
            
            if(val is None): continue
            
            val = get_default(val, key)
            print(val)
        return default(val)  
        
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
    
    def get(self, key:str) -> dict | None:
        
        try:
            value = self.r.get(key)
            self.log.write_info(f"Fetching Key: {key}")
            return json.loads(value)
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return None
    
    def set(self, key:str, value:dict, duration:int = None) -> None:
        
        duration = RedisConnection.MAX_DURATION if(duration is None) else duration
        try:
            jsonText = json.dumps(value)
            self.r.set(key, jsonText, ex=RedisConnection.get_secs_from_minutes(duration))
            self.log.write_info(f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds")
            
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