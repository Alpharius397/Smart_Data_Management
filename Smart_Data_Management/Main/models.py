from copy import copy
import pandas as pd
import pymongo
import pymongo.collection
from typing import NamedTuple, ParamSpec, Union, Iterator, TypedDict
from tools.typesCauseWhyNot import *
from django.conf import settings # type: ignore
from Logs.loggers import MONGO_LOG, REDIS_LOG
import redis
import json

type Condition = dict[str, list | str | int | dict]
type Filter = dict[str, dict[str, list | str | bool | dict] | str | int | bool | list]
type Where = Condition
type Update = Filter
type First = Condition
type Second = Filter
P = ParamSpec("P")

class UniversityHeader:
    
    def __init__(self, university:int, institute:int, branch:int) -> None:
        self.university: int = university
        self.institute: int = institute
        self.branch: int = branch
    
    @staticmethod
    def get(document:dict) -> 'UniversityHeader':
        university:int = Utils.getInt(document, "header", "post", "university")
        institute:int = Utils.getInt(document, "header", "post", "institute")
        branch:int = Utils.getInt(document, "header", "post", "branch")
        
        return UniversityHeader(university, institute, branch)
    
    def to_dict(self) -> dict[str, int]:
        return {
            "university": self.university,
            "institute": self.institute,
            "branch": self.branch,
        }

class Header:
    
    def __init__(self, post: UniversityHeader, uploader:int, manager:list[int]) -> None:
        self.post = post
        self.uploader: int = uploader
        self.manager: list[int] = manager

    @staticmethod
    def get(document:dict) -> 'Header':
        post = UniversityHeader.get(document)
        uploader = Utils.getInt(document, "header", "uploader")
        manager = list(map(int,Utils.getList(document, "header", "manager")))

        return Header(post,uploader,manager)
    
    def to_dict(self) -> dict[str, dict[str, int] | int | list[int]]:
        return {
            "post": self.post.to_dict(),
            "uploader": self.uploader,
            "manager": self.manager
        }
    
class DataHeader:
    
    def __init__(self, columns: list[str], image_columns: list[int], file_name: str) -> None:
        self.columns = columns
        self.image_columns = image_columns
        self.file_name = file_name
    
    @staticmethod
    def get(columns: list[str], image_columns: list[int], file_name: str, **kwargs) -> 'DataHeader':        
        return DataHeader(columns, image_columns, file_name)
    
    def to_dict(self) -> dict[str, list[str] | str | list[int]]:
        return {
            "columns": self.columns,
            "image_columns": self.image_columns,
            "file_name": self.file_name
        }

class Feed:
    
    def __init__(self, locked:bool, issued:bool, time_of_lock:str|None, time_of_issue:str|None, status:bool|None, feed:str|None, index:int) -> None:
        self.locked = locked
        self.issued = issued
        self.time_of_issue = time_of_issue
        self.time_of_lock = time_of_lock
        self.status = status
        self.feed = feed
        self.index = index
        
    @staticmethod
    def get(locked:bool, issued:bool, time_of_lock:str|None, time_of_issue:str|None, status:bool|None, feed:str|None, index:int, **kwargs) -> 'Feed':
        return Feed(locked, issued, time_of_lock, time_of_issue, status, feed, index)
    
    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "locked": self.locked,
            "time_of_lock": self.time_of_lock,
            "issued": self.issued,
            "time_of_issue": self.time_of_issue,
            "status": self.status,
            "feed": self.feed,
            "index": self.index
        }

class RowData:
    
    def __init__(self, row: list[str | int], feed: Feed) -> None:
        self.row = row
        self.feed = feed
        
    @staticmethod
    def get(row: list[str | int], feed: dict[str, str] | dict[str, int] | dict[str, None]):
        return RowData(row, Feed.get(**feed))
    
    def to_dict(self) -> dict[str, list[str | int] | dict[str, str | int | bool | None]]:
        return {
            "row": self.row,
            "feed": self.feed.to_dict()
        }
    
class DataExcel:
    
    def __init__(self, excel: list[RowData], header: DataHeader):
        self.excel = excel
        self.header = header
    
    @staticmethod
    def get(document:dict) -> 'DataExcel':
        
        def default_data_row_dict(x: dict[str, str | list], idx:int):
            row = {'row':[], 'feed':Feed(False,False,None,None,None,None,idx).to_dict()}
            for key,val in x.items():
                if(key in row):
                    row[key] = val
            return row
        
        def default_data_header_dict(x: dict[str, str | list]):
            row = {'columns':[], 'image_columns':[], 'file_name':''}
            for key,val in x.items():
                if(key in row):
                    row[key] = val

            return row

        rows_of_excel = Utils.getList(document, "data", "excel")
        data_header = Utils.getDict(document, "data", "header")
        excel = [RowData.get(**default_data_row_dict(x,idx)) for idx, x in enumerate(rows_of_excel)]
        header = DataHeader.get(**default_data_header_dict(data_header))
        return DataExcel(excel, header)
    
    def to_dict(self) -> dict[str, list[dict[str, list[str | int] | dict[str, str | int | bool | None]]] | dict[str, list[str] | str | list[int]]]:
        return {
            "excel": list(map(lambda x: x.to_dict(), self.excel)),
            "header": self.header.to_dict()
        }

class Document:
    
    def __init__(self, _id:str, header: Header, data: DataExcel) -> None:
        self.header = header
        self.data = data
        self._id = _id
    
    @staticmethod
    def get(document: dict) -> 'Document':
        header = Header.get(document)
        data = DataExcel.get(document)
        _id = Utils.getStr(document, "_id")
        
        return Document(_id, header, data)
    
    def to_dict(self) -> dict[str, str | dict[str, list[dict[str, list[str | int] | dict[str, str | int | bool | None]]] | dict[str, list[str] | str | list[int]]] | dict[str, dict[str, int] | int | list[int]]]:
        return {
            "_id": self._id,
            "data": self.data.to_dict(),
            "header": self.header.to_dict()
        }

class MongoFindQuery(NamedTuple):
    conditions:Condition
    filters: Filter
    
    def __iter__(self) -> Iterator[Condition | Filter]:
        yield self.conditions
        yield self.filters

class MongoUpdateQuery(NamedTuple):
    where:Where
    updates:Update

    def __iter__(self) -> Iterator[Where | Update]:
        yield self.where
        yield self.updates

class MongoDeleteQuery(NamedTuple):
    filters:Condition
    updates:Update
    
    def __iter__(self) -> Iterator[Condition | Update]:
        yield self.filters
        yield self.updates
        
class MongoPipeline(NamedTuple):
    match_pipeline:dict
    search_pipeline:dict
    slice_pipeline:dict
    
    def __iter__(self) -> Iterator[dict]:
        yield self.match_pipeline
        yield self.search_pipeline
        yield self.slice_pipeline

class MegaBFG9000Launcher(NamedTuple):
    match_pipeline: dict
    extract_pipeline: dict
    sort_pipeline: dict
    search_pipeline: dict
    slice_pipeline: dict

    def __iter__(self) -> Iterator[dict]:
        yield self.match_pipeline
        yield self.extract_pipeline
        yield self.sort_pipeline
        yield self.search_pipeline
        yield self.slice_pipeline

class MergeQuery(NamedTuple):
    first: First
    second: Second

    def __iter__(self) -> Iterator[First | Second]:
        yield self.first
        yield self.second
        
class MongoTemplate:
    """
        Data structure:
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
                                time_of_lock,
                                issued,
                                time_of_issue,
                                status,
                                feed,   
                                index
                            }
                        }
                    ],
                    header:{
                        columns,
                        image_columns,
                        file_name
                    }
                }
            }
        }
    """
    def __init__(self) -> None:
        
        self.header:dict[str, dict[str, str | int | None] | list | str | None] = {'post':{'university':None,'institute':None,'branch':None},'uploader':None,'manager':[]}
        self.data_header:dict[str, str | list | None] = {'file_name':None,'image_columns':[],'columns':[]}
        self.data_feed:dict[str, str | int | None] = {'index':0,'locked':None,'time_of_lock':None,'status':None,'feed':None,'time_of_issue':None,'issued':None}
        self.data:list[dict[str, str | list | dict]]= []
        self.feed:dict[str, dict[str,str]] = {}
    
    def __generate_feed_idx(self, idx:int) -> dict[str, str | int | None]:
        temp = copy(self.data_feed)
        temp.update({'index':idx})
        return temp
        
    def add_post(self, university:int,institute:int, branch:int) -> 'MongoTemplate':
        self.header['post'] = {'university':university,'institute':institute,'branch':branch}
        return self
    
    def add_uploader(self, uploader:int) -> 'MongoTemplate':
        self.header['uploader'] = uploader
        return self
    
    def add_file(self, file_name:str) -> 'MongoTemplate':
        self.data_header['file_name'] = file_name
        return self
        
    def add_image(self, image_col:list[int]) -> 'MongoTemplate':
        self.data_header['image_columns'] = image_col
        return self
    
    def add_excel(self, excel:pd.DataFrame) -> 'MongoTemplate':

        self.data = [{'row':list(i[1:]), 'feed':self.__generate_feed_idx(i[0])} for i in excel.itertuples()]

        self.data_header['columns'] = list(excel.columns)
        
        return self
    
    def add_manager(self, managers:list[int]) -> 'MongoTemplate':
        self.header['manager'] = managers
        return self
    
    def get_json(self) -> dict:
        return {'header':self.header,'data':{'excel':self.data,'header':self.data_header}}
    
    @staticmethod
    def _buffer_find_query_factory(column_name:str, start:int, limit:int) -> MongoFindQuery:
        conditions:Condition = {}
        filters:Filter = {}
        
        if(limit==-1):
            filters.update({column_name:{"$slice":[start, 1]}})
            
        else:
            filters.update({column_name:{"$slice":[start, limit]}})

        return MongoFindQuery(conditions, filters)

    @staticmethod
    def _full_find_query_factory(column_name:str) -> MongoFindQuery:
        conditions:Condition = {}
        filters:Filter = {}
        
        filters.update({column_name:1})
        
        return MongoFindQuery(conditions, filters)
    
    @staticmethod
    def _single_update_query(values:dict[str, str | dict | list]) -> MongoUpdateQuery:
        where:Where = {}
        updates:Update = {}
        
        where.update({i:{"$exists":True} for i in values.keys()})
        updates.update({"$set":{column_name:value for column_name, value in values.items() }})
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
    def get_feedback_query(conditions:dict = {}, start:int = 0, limit:int = -1) -> MongoFindQuery:
        res = MongoTemplate._buffer_find_query_factory("data.excel", start, limit)
        res.conditions.update(conditions)
        return res

    @staticmethod
    def get_buffer_query(conditions:dict = {}, start:int = 0, limit:int = -1) -> MergeQuery:
        data_part =  MongoTemplate._buffer_find_query_factory("data.excel", start, limit)
        column_part =  MongoTemplate._full_find_query_factory("data.header")
        header_part =  MongoTemplate._full_find_query_factory("header")
        
        return MongoTemplate.merge_everything(data_part, column_part, header_part,initial_a=conditions)
    
    @staticmethod
    def update_query(where:dict[str, str | dict | list] = {}, updates:dict[str, str | dict | list] = {}) -> MongoUpdateQuery:
        res =  MongoTemplate._single_update_query(updates)
        
        res.where.update(where)
        
        return res

    @staticmethod
    def image_data_update_query(where:dict[str, str | dict | list] = {}, updates:dict[str, str | dict | list] = {}) -> MongoUpdateQuery:
        res =  MongoTemplate._single_update_query(updates)
        
        res.where.update(where)
        
        return res
    
    @staticmethod
    def get_search_buffer_query(condition:dict, column_index:str, locked: str, status: str, issued: str, value:str, start:int, limit:int) -> MongoPipeline:
        
        MAPPING: dict[str, bool | None] = {'true':True, 'false': False, 'none': None}
        
        def state_value(value: str) -> tuple[bool, bool | None]:
            if(value in MAPPING):
                return True, MAPPING[value]
            else:
                return False, None
        
        def int_convert(val: str) -> tuple[bool, int]:
            try:
                return True, int(val)
            except:
                return False, int()
        
        match_pipeline = {"$match":{**condition}}
        
        conditions:list[ dict[str, dict[str, dict[str, list[str | int]] | str] | list ]] =[]
        
        column_flag, column_state = int_convert(column_index)
        locked_flag, locked_state = state_value(locked)
        status_flag, status_state = state_value(status)
        issued_flag, issued_state = state_value(issued)
        
        if(column_flag and value):
            conditions.append(
                {
                    '$regexMatch':{ # column check
                        'input':{
                            '$arrayElemAt':["$$i.row",column_state]
                        },
                        "regex": value,
                        "options": "i"
                    }
                }
            )
            
        if(locked_flag):
            conditions.append(
                {
                    '$eq':[ # locked check
                            '$$i.feed.locked', locked_state                                                            
                        ]
                }
            )
        
        if(status_flag):
            conditions.append(
                {
                    '$eq':[ # status check
                        '$$i.feed.status', status_state                                                            
                    ]
                }
            )
        
        if(issued_flag):
            conditions.append(
                {
                    '$eq':[ # issued check
                        '$$i.feed.issued', issued_state                                                            
                    ]
                }
            )
            
        search_pipeline = {
                            '$project':{
                                "header":1,
                                "data.header":1,
                                "data.excel":{
                                    '$filter':{
                                        'input':"$data.excel",
                                        'as':"i",
                                        'cond':{
                                            "$and": conditions
                                        }
                                    },
                                }
                            }
                        }
        
        slice_pipeline = {
                            '$project':{
                                "data.header":1,
                                "header":1,
                                "data.excel":{
                                    '$slice':["$data.excel", start, limit]
                                },
                            }
                        }
                
        return MongoPipeline(match_pipeline,search_pipeline,slice_pipeline)
    
    @staticmethod
    def get_quick_buffer_query(condition: dict, column_index: int, value: str) -> MegaBFG9000Launcher:
        match_pipeline = {
            "$match": {**condition}
        }

        extract_pipeline = {
            "$project": {
                "option": {
                    "$map": {
                        "input": "$data.excel",
                        "as": "i",
                        "in": {
                            "$arrayElemAt": ["$$i.row", column_index]
                        }
                    }
                }
            }
        }

        search_pipeline = {
            "$project": {
                "option": {
                    "$filter": {
                        "input": "$option",
                        "as": "i",
                        "cond": {
                            "$regexMatch": {
                                "input": "$$i",
                                "regex": value,
                                "options": "i"
                            }
                        }
                    }
                }
            }
        }

        sort_pipeline = {
            "$project": {
                "option": {
                    "$sortArray": {
                        "input": "$option",
                        "sortBy": 1
                    }
                }
            }
        }

        slice_pipeline = {
            "$project": {
                "option": {
                    "$slice": ["$option", 0, 5]
                },
                "_id": 0
            }
        }
        return MegaBFG9000Launcher(match_pipeline,extract_pipeline,sort_pipeline,search_pipeline,slice_pipeline)
    
    @staticmethod
    def merge_everything(*query:MongoFindQuery|MongoDeleteQuery|MongoUpdateQuery|MergeQuery, initial_a:dict = {}, initial_b:dict = {}) -> MergeQuery:
        
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
        self.connection:pymongo.MongoClient = pymongo.MongoClient(settings.MONGO_URL)
        self.collection:pymongo.collection.Collection | None = None
    
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
    
    def find_one(self, condition:dict, filters:dict = {}) -> Document | None:
        res: Document | None = None
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return res
        
        try:
            val = self.collection.find_one(condition,filters)
            self.log.write_info(f"Applying search with filters '{condition}' and displaying '{filters}'")
            
            if(val is None):
                return None

            res = Document.get(val)
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
        
        return res
    
    def find_all(self, condition:dict, filters:dict = {}) -> list[Document]:
        res:list[Document] = []
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return res
        
        try:
            vals = self.collection.find(condition,filters).to_list()
            res = list(map(Document.get, vals))
            self.log.write_info(f"Applying search with filters '{condition}' and displaying '{filters}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
        
        return res
    
    def update_one(self, condition:dict, update:dict) -> bool:
        success:bool = False
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return success
        
        try:
            _ = self.collection.update_one(condition,update)
            print(_)
            success = bool(_.matched_count==1)
            self.log.write_info(f"Applying updation '{update}' to document '{condition}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return success
    
    
    def delete_one(self, condition:dict) -> bool:
        success:bool = False
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return success
        
        try:
            _ = self.collection.delete_one(condition)
            
            success = bool(_.deleted_count==1)
            self.log.write_info(f"Applying deletion to document '{condition}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return success
    
    def insert_one(self, doc:MongoTemplate) -> str | None:
        
        mongoID:str | None = None
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return mongoID
        
        try:
            _ = self.collection.insert_one(doc.get_json())
            mongoID = _.inserted_id
            self.log.write_info(f"Inserting document with mongoID '{mongoID}'")
            
        except Exception as e:            
            self.log.write_error(self.log.get_error_info(e))
            
        return mongoID
    
    def replace_one(self, condition:dict, doc: MongoTemplate) -> bool:
        
        success:bool = False
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return success
        
        try:
            _ = self.collection.replace_one(condition,doc.get_json())
            success = bool(_.matched_count==1)
            self.log.write_info(f"Replacing document with filters '{condition}'")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return success
    
    def close(self) -> None:
        try:
            self.connection.close()
            self.log.write_info("Closing MongoDB connection")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
    
    def aggregate(self, *pipeline:dict[str, Union[dict,str]],) -> list[dict[str, Any]]:
        result:list[dict[str,Any]] = []
        
        if(self.collection is None):
            self.log.write_error("Mongo Connection Failed")
            return result
        
        try: 
            self.log.write_info(f"Aggregating pipeline with {list(pipeline)}")
            result = self.collection.aggregate([*pipeline]).to_list()
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return result

class RedisConnection:
    
    MAX_DURATION:int = 3
    log = REDIS_LOG
    
    def __init__(self) -> None:
        self.r = None
        
    def connect(self) -> 'RedisConnection':
        try:
            self.r = redis.Redis(**settings.REDIS,decode_responses=True) # type: ignore
            self.log.write_info("Connecting to Redis Database")
            
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return self
    
    def get(self, key:str) -> dict:
        
        if(self.r is None):
            return {}
        
        try:
            value = self.r.get(key)
            self.log.write_info(f"Fetching Key: {key}")
            return json.loads(value)
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return {}
    
    def set(self, key:str, value:dict, duration:int = 0) -> bool:
        
        duration = RedisConnection.MAX_DURATION if(duration==0) else duration
        
        if(self.r is None):
            return False
        
        try:
            jsonText = json.dumps(value)
            self.r.set(key, jsonText, ex=RedisConnection.get_secs_from_minutes(duration))
            self.log.write_info(f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds")
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return False
        
    def unset(self, key: str) -> bool:
        
        if(self.r is None):
            return False
        
        try:
            self.r.unlink(key)
            self.log.write_info(f"Unsetting Key: {key}")      
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
            
        return False
    
    def close(self) -> bool:
        
        if(self.r is None):
            return False
        
        try:
            self.r.close()
            self.log.write_info("Closing Redis connection")
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        
        return False
    
    @staticmethod        
    def get_secs_from_minutes(minutes:int) -> int: 
        return minutes*60
