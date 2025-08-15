
from typing import Any, Union

type AllType = str | int | bool | dict | list
type NullStr = str | None
type NullBool = bool | None
type NullInt = int | None
type NullType = AllType | NullBool

class Utils:
    
    @staticmethod
    def __getValue(dictionary: dict, *keyString:Union[str,int]) -> NullType:
        
        def get_default(value: AllType, key:Union[str,int]) -> NullType:
            try:
                if(isinstance(value,dict)):
                    return value.get(key, None)
                elif(isinstance(value, list) and isinstance(key, int)):
                    return value.__getitem__(int(key))
                else:
                    return value
            except Exception as e:
                return None
            
        val: NullType = dictionary # type: ignore
        
        for key in keyString:
            
            if(val is None): return None
            
            val = get_default(val, key) # type: ignore

        return val
    
    @staticmethod
    def getInt(dictionary: dict, *keyString:Union[str,int]) -> int:
        val: Any = Utils.__getValue(dictionary,*keyString)
        
        return int() if (val is None) else int(val) # type: ignore

    @staticmethod
    def getStr(dictionary: dict, *keyString:Union[str,int]) -> str:
        val: Any = Utils.__getValue(dictionary,*keyString)
        
        return str() if (val is None) else str(val) # type: ignore
    
    @staticmethod
    def getList(dictionary: dict, *keyString:Union[str,int]) -> list:
        val: Any = Utils.__getValue(dictionary,*keyString)
        
        return list() if (val is None) else list(val) # type: ignore
    
    @staticmethod
    def getDict(dictionary: dict, *keyString:Union[str,int]) -> dict:
        val: Any = Utils.__getValue(dictionary,*keyString)
        
        return dict() if (val is None) else dict(val) # type: ignore


