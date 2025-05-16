import psycopg2 as psql
import psycopg2.sql as SQL
import re
from datetime import date,time
from errors import *
from typing import Any, NamedTuple

def get_error_info(e:Exception) -> str:
	info = f"{e.__class__.__module__}.{e.__class__.__name__} : {e}"
	print(info)
	return info

    
type INPUT_DATA = int | float | time | date | str | list[str | float | int | date | time]

type DATA = int | float | time | date | str



class Table:
    
    def __init__(self, table_name:str = "test") -> None:
        """ Provide a table name (Pre-existing/new) """
        self.connection = None
        self.table_name = table_name
        self.connectionAttempt = False
        
        self.sql_query = SqlQuery(self)
        """ All Inner Class that perform different work """

    def connectToDB(self,database:str = 'test', user:str = 'postgres', password:str = '1234', host:str = 'localhost', port:int = 5432):
        """ Attempt connection to Database """
        try:
            self.connection = psql.connect(database=database,user=user,password=password,host=host,port=port)

        except Exception as e:
            get_error_info(e)
            raise ConnectionFailed() from e

        finally:
            self.connectionAttempt = True

        return self

    def check_connection(self) -> psql.extensions.cursor:
        """ Checks connection and returns a cursor """
        if(self.connection):
            print("Connection Established")
            return self.connection.cursor()

        if(self.connectionAttempt):
            print("Connection Not Established")
            raise ConnectionFailed()
        else:
            print("Run connectToDB first!")
            raise EstablishConnection()

    def do_sql_query(self, cursor:psql.extensions.cursor, sql:str|SQL.Composed) -> None:
        """ Used to open a cursor, perform sql query, commit and close the cursor """
        cursor.execute(sql)
        self.connection.commit()
        cursor.close()

    def do_sql_queries(self, cursor:psql.extensions.cursor, sql:list[str | SQL.Composed]) -> None:
        """ Used to open a cursor, perform multiple sql queries, commit and close the cursor """
        for query in sql:   
            cursor.execute(query)
        self.connection.commit()
        cursor.close()
    
    def do_sql_and_get_all(self, cursor: psql.extensions.cursor, sql: str|SQL.Composed) -> list[tuple[Any,...]]:
        """ Used to open a cursor, perform sql query and return the result, commit and close the cursor """
        cursor.execute(sql)
        result = cursor.fetchall()
        self.connection.commit()
        cursor.close()
        return result

    def create_table(self, auto_pk:bool=True) -> bool:
        """ Make a new table with an optional one auto increement column ( __id__ ) as primary key """
        sql = SQL.SQL('create table {} (%s);' % (lambda auto_pk:'__id__ serial primary key not null' if auto_pk else '')(auto_pk)).format(SQL.Identifier(self.table_name),)

        cursor = self.check_connection()	
        try:
            self.do_sql_query(cursor,sql)
            return True

        except psql.errors.DuplicateTable as e:
            get_error_info(e)
            raise DuplicateTable(self.table_name)

        except psql.errors.InsufficientPrivilege as e:
            get_error_info(e)
            raise UnauthorizedAction(self.table_name,"create table")

        except Exception as e:
            get_error_info(e)
            raise e

        finally:
            if self.connection: self.connection.rollback()
            
    
    def rename_table(self, new_name:str) -> bool:
        """ Rename table to a new name """
        sql = SQL.SQL('alter table {} rename to {};').format(SQL.Identifier(self.table_name),SQL.Identifier(new_name))

        cursor = self.check_connection()	
        try:
            self.do_sql_query(cursor,sql)
            return True

        except psql.errors.DuplicateTable as e:
            get_error_info(e)
            raise DuplicateTable(self.table_name)

        except psql.errors.InsufficientPrivilege as e:
            get_error_info(e)
            raise UnauthorizedAction(self.table_name,"alter table")

        except Exception as e:
            get_error_info(e)
            raise e

        finally:
            if self.connection: self.connection.rollback()
            
    def drop_table(self, safe:bool = True,you_sure:bool = False, you_sure_2:bool = False) -> bool:
        """ Drops the table """
        
        sql = SQL.SQL('drop table {table_name} %(safe)s;' % {'safe':(lambda safe:'cascade' if (not safe) else 'restrict')(safe)}).format(table_name=SQL.Identifier(self.table_name))
        res = you_sure and you_sure_2
        cursor = self.check_connection()

        try:
            if res: self.do_sql_query(cursor,sql)
            return True

        except psql.errors.UndefinedTable as e:
            get_error_info(e)
            raise TableNotFound(self.table_name)	
    
        except psql.errors.InsufficientPrivilege as e:
            get_error_info(e)
            raise UnauthorizedAction(self.table_name,"drop table")

        except Exception as e:
            get_error_info(e)
            raise e

        finally:
            if self.connection: self.connection.rollback()
            
class Helper:
    """ Class that contains helper functions """
    DATA_TYPE = ['int','char','date','time','float','int[]','char[]','date[]','time[]','float[]']
    
    class DataType(NamedTuple):
        """ A sample object with two properties: data_type, is_array """
        data_type:str
        is_array:bool
        
    class DBType(NamedTuple):
        """ A sample object with two properties: column_name, data_type, udt_name """
        column_name:str
        data_type:str
        udt_name:str
    
    def get_db_type(col_type:str, dtype:str) -> 'Helper.DataType':
        """ Extracts the Datatype of columns from database """

        int_check = True if re.match(r'(\w*)int',dtype) else False
        float_check = True if re.match(r'(\w*)(float|numeric)',dtype) else False
        date_check = True if re.match(r'(\w*)date',dtype) else False
        time_check = True if re.match(r'(\w*)time',dtype) else False
        varchar_check = True if re.match(r'(\w*)char',dtype) else False
        array_check = True if re.match(r'(\w*)ARRAY',col_type) else False
        
        if int_check: return Helper.DataType(data_type="int",is_array=array_check)
        elif float_check: return Helper.DataType(data_type="float",is_array=array_check)
        elif varchar_check: return Helper.DataType(data_type="char",is_array=array_check)
        elif time_check: return Helper.DataType(data_type="time",is_array=array_check)
        elif date_check: return Helper.DataType(data_type="date",is_array=array_check)

        print("Wrong Datatype found")
        raise DataTypeNotSupported(dtype,Helper.DATA_TYPE)
    
    def get_default(type:str) -> DATA:
        """ Get the default value for a data-type """
        match type:
            case"int": return 0
            case"float": return 0.0
            case"char": return '0'
            case"date": return date(2024,1,1)
            case"time": return time(0,0,0)
            case _: raise DataTypeNotSupported(type,Helper.DATA_TYPE)	
            
    def _make_map(arr:list[DBType]) -> dict[str,DataType]:
        """ Helper functions to map column to appropriate data type """
        memo = {}
        for column_name,data_type,udt_name in arr:
            memo[column_name] = Helper.get_db_type(data_type,udt_name)
        return memo
    
    def get_type(type:str) -> str:
        """ Converts input type to database counterpart """
        type, array_part = re.findall(r'(\w+)(\[\])?',type)[0]

        match(type):
            case "int": return f"int{array_part}"
            case "float": return f"decimal{array_part}"
            case "char": return f"varchar{array_part}"
            case "date": return f"date{array_part}"
            case "time": return f"time{array_part}"
            case _: raise DataTypeNotSupported(type,Helper.DATA_TYPE)

    def get_class_type(val:str) -> DATA:
        """ Returns appropriate class for a data type (To check for type) """
        data_type = re.findall(r'(\w+)(\[\])?$',val)

        val, _ = data_type[0]
        match val:
            case "int": return int
            case "float": return float
            case "char": return str
            case "time": return time
            case "date": return date
            case _: raise DataTypeNotSupported(val,Helper.DATA_TYPE)
    
    def data_type_check(memo:'Helper.DataType', val:DATA) -> bool:
        """ Performs data-type checking """
        data_type, is_array = memo.data_type, memo.is_array

        data_type = Helper.get_class_type(data_type)

        if is_array:
            if not ((isinstance(val,list)) and len(val)>0 and all([isinstance(i,data_type) for i in val])): return False
        else:
            if not ((isinstance(val,data_type))): return False

        return True
    
    def get_data_type(type:str) -> str:
        """ Converts input data type into database equivalent data type (wrapper of get_type) """

        if( not type ): raise EmptyValueDetected("Type string is empty") 

        return Helper.get_type(type)
        
    def get_default_value(type:str) -> str:
        """ Gets the default value of a type """
        is_array = True if re.match(r'(\w+)\[\]$',type) else False

        if is_array:
            return f"ARRAY[]::{Helper.get_type(type)}"
        else:
            return f"{Helper.get_default(type)}"
        
class QueryBuilder:
    """ Class that helps in query building """
    
    NAMING_REGEX = r"[^a-zA-z0-9_]"
    
    def nullable(null:bool, type:str) -> str:
        """ Sets column to either null or not dull with a default value """
        return f"not null default {Helper.get_default_value(type)}" if not null else ""

    def data_type(auto_increement:bool, type:str) -> str:
        """ Sets column to auto increement or to a data type of choosing """
        return "serial" if auto_increement else f"{Helper.get_data_type(type)}"
    
    def get_unique_constraint_name(table_name:str, column:str) -> str:
        table = re.sub(QueryBuilder.NAMING_REGEX,"_",table_name)
        col = re.sub(QueryBuilder.NAMING_REGEX,"_",column)
        return "{}_{}_unique".format(table,col)

    def get_unique_sql(name:str, table:str,cursor: psql.extensions.cursor) -> str:
        """ Adds a primary key constraint to the column  """
        return SQL.SQL("alter table {} add constraint {} unique ({});").format(SQL.Identifier(table),SQL.Identifier(QueryBuilder.get_unique_constraint_name(table,name)),SQL.Identifier(name)).as_string(cursor)
    
    def get_primary_key_constraint_name(table_name:str, column:str) -> str:
        table = re.sub(QueryBuilder.NAMING_REGEX,"_",table_name)
        col = re.sub(QueryBuilder.NAMING_REGEX,"_",column)
        return "{}_{}_pkey".format(table,col)
    
    def get_primary_sql(name:str, table:str,cursor: psql.extensions.cursor) -> str:
        """ Adds a primary key constraint to the column  """
        return SQL.SQL("alter table {} add constraint {} primary key ({});").format(SQL.Identifier(table),SQL.Identifier(QueryBuilder.get_primary_key_constraint_name(table,name)),SQL.Identifier(name)).as_string(cursor)

    def get_foreign_key_constraint_name(table_name:str, column:str, table_2:str) -> str:
        table_1_name = re.sub(QueryBuilder.NAMING_REGEX,"_",table_name)
        col = re.sub(QueryBuilder.NAMING_REGEX,"_",column)
        table_2_name = re.sub(QueryBuilder.NAMING_REGEX,"_",table_2)
        
        return "{}_{}_{}_fkey".format(table_1_name,col,table_2_name)
    
    def data_assign_query(dict:dict[str,str]) -> str: 
        """ Helper function to get the data assignment query. Unsure that dict items are parameterized first """
        return f"{'and'.join([f'{i}={j}' for i,j in dict.items()])}"

    def generate_data_query(values:dict[str,INPUT_DATA], data_type: dict[str,Helper.DataType], cursor: psql.extensions.cursor) -> dict[str,str]:
        """ Generates query elements (Parameterized) for value insertion / selection / deletion """
        query = {}
        
        for col,val in values.items():
            dtype, is_array = data_type[col]
            
            if (is_array):
                sub_query = SQL.SQL("ARRAY[{}]").format(SQL.SQL(',').join([SQL.SQL("{val}::%(dtype)s" % {'dtype':Helper.get_data_type(dtype)}).format(val=SQL.Literal(i)) for i in val])).as_string(cursor)
            else:
                sub_query = SQL.SQL("{val}::%(dtype)s" % {'dtype':dtype}).format(val=SQL.Literal(val)).as_string(cursor)

            query[col] = sub_query

        return query

class SqlQuery:
    """ Contains classes to perform different types of queries """
    
    def __init__(self, table: Table):
        self.table_info = self.TableInfo(table)
        self.insert = self.Insert(table)
        self.checker = self.TypeChecker(self.table_info)
        self.update = self.UpdateTable(table)
        self.delete = self.DeleteTable(table)
        self.alter = self.AlterTable(table)
        
    class TableInfo:
        """ Class that gets info about table """
        
        def __init__(self, table: Table):
            self.table = table
            
        def get_nullable(self) -> set[str]:
            """ Get the columns which accept null values (Used for foreign key changes) """
            sql = SQL.SQL("select column_name from information_schema.columns where table_name={table_name} and is_nullable='YES'").format(table_name=SQL.Literal(self.table.table_name))
            cursor = self.table.check_connection()
            result:set[str] = set()

            try:
                arr = self.table.do_sql_and_get_all(cursor,sql)
                
                for i in arr: result.add(i[0])

                return result

            except psql.errors.InsufficientPrivilege as e:
                get_error_info(e)
                raise UnauthorizedAction(self.table.table_name,"select table")
            
            except Exception as e:
                get_error_info(e)
                raise e

            finally:
                if(self.table.connection): self.table.connection.rollback()
                
        
        def get_default(self) -> set[str]:
            """ Get the columns which has default values set """
            sql = SQL.SQL("select column_name from information_schema.columns where table_name={table_name} and column_default is not NULL").format(table_name=SQL.Literal(self.table.table_name))
            cursor = self.table.check_connection()
            result:set[str] = set()

            try:
                arr = self.table.do_sql_and_get_all(cursor,sql)

                for i in arr: result.add(i[0])

                return result

            except psql.errors.InsufficientPrivilege as e:
                get_error_info(e)
                raise UnauthorizedAction(self.table.table_name,"select table")
            
            except Exception as e:
                get_error_info(e)
                raise e

            finally:
                if(self.table.connection): self.table.connection.rollback()
                
                
        def get_unique_keys(self) -> dict[str, str]:
            """ Gets unique keys of the table """
            sql = SQL.SQL("select kc.column_name, kc.constraint_name from information_schema.table_constraints tc join information_schema.key_column_usage kc on kc.table_name = tc.table_name and kc.table_schema = tc.table_schema and kc.constraint_name = tc.constraint_name where tc.constraint_type = 'UNIQUE' and tc.table_name={table_name} and kc.ordinal_position is not null;").format(table_name=SQL.Literal(self.table.table_name))
            cursor = self.table.check_connection()
            result:dict[str,set[str]] = {}

            try:
                unique_keys = self.table.do_sql_and_get_all(cursor,sql)
                
                for col,constraint in unique_keys:
                    if(col not in result): result[col] = set()
                    result[col].add(constraint)
                    
                return result   # { column_name:set(all constraint_name) }

            except Exception as e:
                get_error_info(e)
                raise e
        
            finally:
                if self.table.check_connection: self.table.connection.rollback()
                
                
        def get_primary_key(self) -> dict[str, str]:
            """ Get primary key of the table """
            sql = SQL.SQL("select kc.column_name, kc.constraint_name from information_schema.table_constraints tc join information_schema.key_column_usage kc on kc.table_name = tc.table_name and kc.table_schema = tc.table_schema and kc.constraint_name = tc.constraint_name where tc.constraint_type = 'PRIMARY KEY' and tc.table_name={table_name} and kc.ordinal_position is not null;").format(table_name=SQL.Literal(self.table.table_name))
            cursor = self.table.check_connection()

            try:
                primary_keys = self.table.do_sql_and_get_all(cursor,sql)
                return {col:constraint for col, constraint in primary_keys} # { column_name:constraint_name }

            except Exception as e:
                get_error_info(e)
                raise e

            finally:
                if self.table.check_connection: self.table.connection.rollback()
                

        def get_foreign_keys(self) -> dict[str, set[str]]:
            """ Gets foreign keys of the table """
            sql = SQL.SQL("select column_name,constraint_name from information_schema.table_constraints tc join information_schema.key_column_usage kc on kc.table_name = tc.table_name and kc.table_schema = tc.table_schema and kc.constraint_name = tc.constraint_name where tc.constraint_type = 'FOREIGN KEY' and tc.table_name={table_name} and kc.ordinal_position is not null;").format(table_name=SQL.Literal(self.table.table_name))
            cursor = self.table.check_connection()
            result:dict[str,set[str]] = {}
            
            try:
                foreign_keys = self.table.do_sql_and_get_all(cursor,sql)

                for col, constraint in foreign_keys:
                    if col not in result: result[col] = set()
                    result[col].add(constraint)
    
                return result
    
            except Exception as e:
                get_error_info(e)
                raise e
        
            finally:
                if self.table.connection: self.table.connection.rollback()
                

        def get_columns(self) -> dict[str,Helper.DataType]:
            """ Gets column data-type of all columns """

            sql = SQL.SQL("select column_name,data_type,udt_name from information_schema.columns where table_name={table_name};").format(table_name=SQL.Literal(self.table.table_name))
            
            table_desc:dict[str,Helper.DataType] = {}

            cursor = self.table.check_connection()

            try:
                arr = self.table.do_sql_and_get_all(cursor,sql)
                table_desc = Helper._make_map(arr)
                return table_desc

            except psql.errors.InsufficientPrivilege as e:
                get_error_info(e)
                raise UnauthorizedAction(self.table.table_name,"select table")

            except Exception as e:
                get_error_info(e)
                raise e

            finally:
                if self.table.connection: self.table.connection.rollback()
                
                
        def table_check(self) -> bool:
            """ Checks if table exist or not """
            sql = SQL.SQL("select table_name from information_schema.tables where table_name={table_name};").format(table_name=SQL.Literal(self.table.table_name))

            cursor = self.table.check_connection()
            try:
                arr = self.table.do_sql_and_get_all(cursor,sql)
                return len(arr)>0
            
            except Exception as e:
                get_error_info(e)
                raise e

            finally:
                if self.table.connection: self.table.connection.rollback()
                
    class Insert:
        """ Class that handles insertion of data """
        def __init__(self, table: Table) -> None:
            self.table = table
            self.info = SqlQuery.TableInfo(table)
            self.checker = SqlQuery.TypeChecker(self.info)
            
        def insert_row(self, val:dict[str,INPUT_DATA]) -> bool:
            """ Inserts row into tables """
            if(self.checker.check_value(val)):
                memo = self.info.get_columns()
                cursor = self.table.check_connection()

                values_part:dict[str, str] = QueryBuilder.generate_data_query(val,memo,cursor)
                columns = val.keys()
                insert_query = SQL.SQL("insert into {table_name}({col}) values (%(val)s)" % {'val':','.join(values_part.values())}).format(table_name=SQL.SQL(self.table.table_name),col=SQL.SQL(',').join(map(SQL.Identifier,columns)))

                try:
                    self.table.do_sql_query(cursor,insert_query)
                    return True

                except psql.errors.UndefinedTable as e:
                    get_error_info(e)
                    raise TableNotFound(self.table.table_name)

                except psql.errors.UniqueViolation as e:
                    get_error_info(e)
                    raise UniqueKeyViolation()

                except psql.errors.InsufficientPrivilege as e:
                    get_error_info(e)
                    raise UnauthorizedAction(self.table.table_name,"insert into")

                except Exception as e:
                    get_error_info(e)
                    raise e
                finally:
                    if self.table.connection: self.table.connection.rollback()
            else:
                raise TypeError("One of the value's data type does not match table's column data type")

    class TypeChecker:
        """ Handles data-type validation, column checking etc """
        
        def __init__(self, info: 'SqlQuery.TableInfo') -> None:
            self.info = info
        
        def check_value(self,val:dict[str,INPUT_DATA]) -> bool:
            """ Performs column-value validation """

            memo = self.info.get_columns()
            if(not val): raise EmptyValueDetected("Data Dict")

            for i,j in val.items():
                if i not in memo: raise ColumnNotFound(i)
                if(not Helper.data_type_check(memo[i],j)): raise DataTypeMismatch(i,memo[i],j)

            return True
        
        def check_columns(self,cols:list[str]) -> bool:
            """ Checks if columns are present in table or not """
            memo = self.info.get_columns()

            if(not cols): raise EmptyValueDetected("List of Columns")

            for i in cols:
                if i not in memo: raise ColumnNotFound(i)
            
            return True

    class UpdateTable:
        """ Class handling updation of data. (Uses eq check for updation) """

        def __init__(self, table: Table) -> None:
            self.table = table
            self.info = SqlQuery.TableInfo(table)
            self.checker = SqlQuery.TypeChecker(self.info)
            
        
        def update_row(self, val:dict[str, INPUT_DATA], where:dict[str, INPUT_DATA]) -> bool:
            """ Updates column data with val where the condition (where) is true (Where only supports ==/eq check) """

            val_check = self.checker.check_value(val)
            where_check = self.checker.check_value(where)

            if(val_check and where_check):
                memo = self.info.get_columns()
                cursor = self.table.check_connection()
    
                where_part = QueryBuilder.generate_data_query(where,memo,cursor)
                set_part = QueryBuilder.generate_data_query(val,memo,cursor)

                update_query = SQL.SQL("update {table_name} set %(set)s where %(where)s" % {'set':QueryBuilder.data_assign_query(set_part),'where':QueryBuilder.data_assign_query(where_part)}).format(table_name=SQL.Identifier(self.table.table_name))

                try:
                    self.table.do_sql_query(cursor,update_query)
                    return True

                except psql.errors.UndefinedTable:
                    get_error_info(e)
                    raise TableNotFound(self.table.table_name)
        
                except psql.errors.InsufficientPrivilege as e:
                    get_error_info(e)
                    raise UnauthorizedAction(self.table.table_name,"update")

                except psql.errors.UniqueViolation as e:
                    get_error_info(e)
                    raise UniqueKeyViolation()

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally: 
                    if self.table.connection: self.table.connection.rollback()
                
            elif(where_check):
                raise TypeError("One of the value's data type does not match table's column data type")
            
            elif(val_check):
                raise TypeError("One of the where's data type does not match table's column data type")
            
            else:
                raise TypeError("One of the where's and value's data type does not match table's column data type")
        
    class DeleteTable:
        """ Class handles deletion of a row from table """
        
        def __init__(self, table: Table) -> None:
            self.table = table
            self.info = SqlQuery.TableInfo(table)
            self.checker = SqlQuery.TypeChecker(self.info)
            
            
        def delete_row(self, where:dict[str, INPUT_DATA]) -> bool:
            """ Deletes column data with val where the condition (where) is true (Where only supports  __==__/__eq__ check) """
            
            if(self.checker.check_value(where)):
                memo = self.info.get_columns()
                cursor = self.table.check_connection()
                where_part = QueryBuilder.generate_data_query(where,memo,cursor)
        
                delete_query = SQL.SQL("delete from {table_name} where %(where)s" % {'where':QueryBuilder.data_assign_query(where_part)}).format(table_name=SQL.Identifier(self.table.table_name))

                try:
                    self.table.do_sql_query(cursor,delete_query)
                    return True

                except psql.errors.UndefinedTable as e:
                    get_error_info(e)
                    raise TableNotFound(self.table.table_name)

                except psql.errors.UniqueViolation as e:
                    get_error_info(e)
                    raise UniqueKeyViolation()
        
                except psql.errors.InsufficientPrivilege as e:
                    get_error_info(e)
                    raise UnauthorizedAction(self.table.table_name,"delete from")

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally: 
                    if self.table.connection: self.table.connection.rollback()
            else:
                raise TypeError("One of the where's data type does not match table's column data type")

    class AlterTable:
        """ Class handles alteration of table structure (columns and constraint) """
        
        def __init__(self, table: Table) -> None:
            self.table = table
            self.info = SqlQuery.TableInfo(table)
            self.checker = SqlQuery.TypeChecker(self.info)
            self.column_alter = SqlQuery.AlterTable.ColumnAlter(self.table, self.info, self.checker)
            self.constraint_alter = SqlQuery.AlterTable.ConstraintAlter(self.table, self.info, self.checker)
            
        class ColumnAlter:
            """ Class that handles alteration of column structure """
            
            def __init__(self, table: Table, info: 'SqlQuery.TableInfo', checker: 'SqlQuery.TypeChecker') -> None:
                self.info = info
                self.table = table
                self.checker = checker
                
            def add_column(self, name:str = 'col', type:str = "char", unique_key=False, primary_key=False,null=True, auto_increement=False) -> bool:
                """ Adds a new column into the database """
            
                if (not name): raise EmptyValueDetected("Column Name")
                if (auto_increement and null): raise ConflictingCondition(name,"auto increement","null")
                if (unique_key and null): raise ConflictingCondition(name,"unique","null")
                if (primary_key and null): raise ConflictingCondition(name,"primary key","null")
                if (primary_key and unique_key): raise ConflictingCondition(name,"primary key","unique")
                if (primary_key and self.info.get_primary_key()): raise PrimaryKeyExists(self.table.table_name)
                
                cursor = self.table.check_connection()
                add_sql = SQL.SQL("alter table {table} add column {name} %(data_type)s %(nullable)s;" % {'data_type':QueryBuilder.data_type(auto_increement,type),'nullable':QueryBuilder.nullable(null,type)}).format(table=SQL.Identifier(self.table.table_name),name=SQL.Identifier(name))

                primary_sql = QueryBuilder.get_primary_sql(name,self.table.table_name,cursor)
                unique_sql = QueryBuilder.get_unique_sql(name,self.table.table_name,cursor)
                
                to_do_sql = [add_sql]
                
                if(unique_key): to_do_sql.append(unique_sql)
                elif(primary_key): to_do_sql.append(primary_sql)
            
                try:
                    self.table.do_sql_queries(cursor, to_do_sql)
                    return True

                except psql.errors.UndefinedTable as e:
                    get_error_info(e)
                    raise TableNotFound(self.table.table_name)

                except psql.errors.DuplicateColumn as e:
                    get_error_info(e)
                    raise DuplicateColumn(name)

                except psql.errors.InsufficientPrivilege as e:
                    get_error_info(e)
                    raise UnauthorizedAction(self.table.table_name,"alter table / insert into")

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally:
                    if self.table.connection: self.table.connection.rollback()
                    
            def change_column_name(self, old_name:str, new_name:str) -> bool:
                """ Change column's name to a new name """
                sql = SQL.SQL("alter table {table_name} rename column {old_name} to {new_name};").format(table_name=SQL.Identifier(self.table.table_name),old_name=SQL.Identifier(old_name),new_name=SQL.Identifier(new_name))
                cursor = self.table.check_connection()
                col_check = self.checker.check_columns([old_name])

                if(col_check):
                    try:
                        self.table.do_sql_query(cursor,sql)
                        return True

                    except psql.errors.UndefinedTable as e:
                        get_error_info(e)
                        raise TableNotFound()

                    except psql.errors.DuplicateColumn as e:
                        get_error_info(e)
                        raise DuplicateColumn(new_name)

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")
            
                    except Exception as e:
                        get_error_info(e)		
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
                
                return False
                
                
            def change_data_type(self, column:str, type:str) -> bool:
                """ Changes column data type to given type and also updates default value """
                
                col_check = self.checker.check_columns([column])
                dtype_1, dtype_2 = (lambda x: f"{x[0]}{'[]' if x[1] else ''}")(self.info.get_columns()[column]), Helper.get_data_type(type)

                is_array = True if re.match(r'(\w+)\[\]$',dtype_2) else False
        
                default_columns = self.info.get_default()
        
                sql = SQL.SQL("alter table {table_name} alter column {column} type %(dtype_2)s using %(using)s::%(dtype_2)s;" % {'dtype_2':dtype_2,'using':(lambda is_array: 'ARRAY[{column}]' if is_array else '{column}')(is_array)}).format(table_name=SQL.Identifier(self.table.table_name), column=SQL.Identifier(column))
        
                drop_def_sql = SQL.SQL("alter table {} alter column {} drop default;").format(SQL.Identifier(self.table.table_name), SQL.Identifier(column))
        
                set_def_sql = SQL.SQL("alter table {table_name} alter column {column} set default %(dtype)s" % {'dtype':Helper.get_default(type)}).format(table_name=SQL.Identifier(self.table.table_name),column=SQL.Identifier(column))
        
                to_do_sql = [sql]
                
                if(column in default_columns): to_do_sql = [drop_def_sql] + to_do_sql + [set_def_sql]
        
                cursor = self.table.check_connection()

                if(col_check):
                    try:
                        self.table.do_sql_queries(cursor, to_do_sql)
                        return True

                    except psql.errors.DatatypeMismatch as e:
                        get_error_info(e)
                        raise DataConversionError(dtype_1,dtype_2)

                    except psql.errors.UndefinedTable as e:
                        get_error_info(e)
                        raise TableNotFound(self.table.table_name)

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)	
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
                        
                
                return False
                
            def drop_column_default(self, col:str) -> bool:
                """ Drops the default value for a column """
                
                col_check = self.checker.check_columns([col])
                sql = SQL.SQL("alter table {} alter column {} drop default;").format(SQL.Identifier(self.table.table_name), SQL.Identifier(col))
                cursor = self.table.check_connection()
                
                if(col_check):
                
                    try:
                        self.table.do_sql_query(cursor,sql)
                        return True

                    except psql.errors.UndefinedTable as e:
                        get_error_info(e)
                        raise TableNotFound(self.table.table_name)

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e
            
                    finally:
                        if(self.table.connection): self.table.connection.rollback()

                return False
            
            def set_column_default(self, column_name:str, def_value:INPUT_DATA) -> bool:
                """ Sets default value of a column  """
                col_check = self.checker.check_value({column_name:def_value})
                cursor = self.table.check_connection()

                dtype = QueryBuilder.generate_data_query({column_name:def_value},self.info.get_columns(),cursor)[column_name]

                sql = SQL.SQL("alter table {table_name} alter column {column} set default %(dtype)s" % {'dtype':dtype}).format(table_name=SQL.Identifier(self.table.table_name),column=SQL.Identifier(column_name))

                default_columns = self.info.get_default()

                if(column_name in default_columns): raise DefaultValueExists(column_name)

                if(self.info.table_check() and col_check):
                    try:
                        self.table.do_sql_query(cursor, sql)
                        return True

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
            
                return False
            

            def drop_column_not_null(self, column_name:str) -> bool:
                """ Set column as nullable """
                col_check = self.checker.check_columns([column_name])
                cursor = self.table.check_connection()
                sql = SQL.SQL("alter table {table_name} alter column {column} drop not null").format(table_name=self.table.table_name,column=SQL.Identifier(column_name))

                null_columns = self.info.get_nullable()
                primary_key = self.info.get_primary_key()

                if(column_name in primary_key): raise NullNotAccepted(f'{column_name} (Primary Key)')
                if(column_name in null_columns): raise NullAccepted(column_name)

                if(self.info.table_check() and col_check):
                    try:
                        self.table.do_sql_query(cursor, sql)
                        return True

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
            
                return False
            
            def set_column_not_null(self, column_name:str) -> bool:
                """ Sets column as not null """
                col_check = self.checker.check_columns([column_name])
                cursor = self.table.check_connection()
                sql = SQL.SQL("alter table {table_name} alter column {column} set not null").format(table_name=self.table.table_name,column=SQL.Identifier(column_name))

                null_columns = self.info.get_nullable()

                if(column_name not in null_columns): raise NullNotAccepted(column_name)

                if(self.info.table_check() and col_check):
                    try:
                        self.table.do_sql_query(cursor, sql)
                        return True

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
            
                return False
            
        class ConstraintAlter:
            """ Class that handles alteration of constraint structure """
            FOREIGN_KEY_OPTION = {'restrict','cascade','null','none','default'}
            
            def __init__(self, table: Table, info: 'SqlQuery.TableInfo', checker: 'SqlQuery.TypeChecker') -> None:
                self.info = info
                self.table = table
                self.checker = checker
                
            def change_option(self, option:str):
                match option:
                    case 'restrict': return "restrict"
                    case 'cascade': return "cascade"
                    case 'null': return "set null"
                    case 'none': return "no action"
                    case 'default': return "set default"
                    case _: raise InvalidOperation(option, self.FOREIGN_KEY_OPTION)

            def drop_constraint(self, constraint:str, safe:bool = True) -> bool:
                """ Wrapper function to drop constraint """
                sql = SQL.SQL("alter table {table_name} drop constraint %(constraint)s %(option)s" % {'constraint':constraint,'option':(lambda safe:'cascade' if (not safe) else 'restrict')(safe)}).format(table_name=SQL.Identifier(self.table.table_name))
            
                cursor = self.table.check_connection()
                
                try:
                    self.table.do_sql_query(cursor,sql)
                    return True

                except psql.errors.UndefinedTable as e:
                    raise TableNotFound(self.table.table_name)

                except psql.errors.UndefinedObject as e:
                    raise ConstraintNotFound(constraint,self.table.table_name)

                except psql.errors.InsufficientPrivilege as e:
                    raise UnauthorizedAction(self.table.table_name,"alter table")

                except Exception as e:
                    raise e

                finally:
                    if(self.table.connection): self.table.connection.rollback()
                    
                    
            def drop_primary_key(self, safe:bool = True) -> bool:
                """ Drops primary key of the table """
                primary_key = self.info.get_primary_key()

                if(not primary_key): raise PrimaryKeyDoesNotExists(self.table.table_name)

                primary_key_constraint = list(primary_key.values())[0]
                
                try:
                    return self.drop_constraint(primary_key_constraint,safe)

                except ConstraintNotFound as e:
                    get_error_info(e)
                    raise ConstraintNotFound(*e.args,'primary')

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally:
                    if(self.table.connection): self.table.connection.rollback()

            def drop_foreign_key(self, constraint:str, safe:bool = True) -> bool:
                """ Drops foreign key(s) of the table """
                
                foreign_key = self.info.get_foreign_keys()

                if(constraint not in foreign_key): raise ConstraintNotFound(constraint,self.table.table_name,'foreign key')

                foreign_key_constraint = foreign_key[constraint]
                
                try:
                    return self.drop_constraint(foreign_key_constraint,safe)

                except TableNotFound as e:
                    get_error_info(e)
                    raise e

                except ConstraintNotFound as e:
                    get_error_info(e)
                    raise ConstraintNotFound(*e.args,'foreign key')

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally:
                    if(self.table.connection): self.table.connection.rollback()

            def drop_unique_key(self, constraint:str, safe:bool = True) -> bool:
                unique_key = self.info.get_unique_keys()

                if(constraint not in unique_key): raise ConstraintNotFound(constraint,self.table.table_name,'unique')

                unique_key_constraint = unique_key[constraint]
                try:
                    return self.drop_constraint(unique_key_constraint,safe)

                except ConstraintNotFound as e:
                    get_error_info(e)
                    raise ConstraintNotFound(*e.args,'unique')

                except Exception as e:
                    get_error_info(e)
                    raise e

                finally:
                    if(self.table.connection): self.table.connection.rollback()
                    
                
            def add_primary_key(self, column_name:str) -> bool:
                """ Adds primary key to table """
            
                if(self.info.get_primary_key()): raise PrimaryKeyExists(self.table.table_name)

                cursor = self.table.check_connection()
                col_check = self.checker.check_columns([column_name])
                sql = QueryBuilder.get_primary_sql(column_name,self.table.table_name,cursor)

                if(self.info.table_check() and col_check):
                    try:
                        self.table.do_sql_query(cursor,sql)
                        return True

                    except psql.errors.DuplicateTable as e:
                        get_error_info(e)
                        raise DuplicateConstraint(QueryBuilder.get_primary_key_constraint_name(column_name))

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
            
                return False

            def add_unique_key(self, column_name:str) -> bool:
                """ Adds unique key to table """

                col_check = self.checker.check_columns([column_name])
                cursor = self.table.check_connection()
                sql = QueryBuilder.get_unique_sql(column_name,self.table.table_name,cursor)

                existing_constraint = self.info.get_unique_keys()

                if(column_name in existing_constraint): raise ConstraintTypeExists(column_name,'unique')

                if(self.info.table_check() and col_check):
                    try:
                        self.table.do_sql_query(cursor, sql)
                        return True

                    except psql.errors.DuplicateTable as e:
                        get_error_info(e)
                        raise DuplicateConstraint(QueryBuilder.get_unique_constraint_name(column_name))

                    except psql.errors.InsufficientPrivilege as e:
                        get_error_info(e)
                        raise UnauthorizedAction(self.table.table_name,"alter table")

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()
            
                return False
                    
                    
            def add_foreign_key(self, foreign_table:'Table', name:str, on_delete:str = 'restrict', on_update:str= 'restrict') -> bool:
                """ Add foreign key into table """
                primary_of_other = list(foreign_table.sql_query.table_info.get_primary_key().keys())

                if(not primary_of_other): raise PrimaryKeyDoesNotExists(foreign_table.table_name)
                primary_of_other = primary_of_other[0]
                cursor = self.table.check_connection()

                col_check = self.checker.check_columns([name])
                constraint_name = QueryBuilder.get_foreign_key_constraint_name(self.table.table_name,name,foreign_table.table_name)
                existing_foreign = self.info.get_foreign_keys()
        
                if(name in existing_foreign and constraint_name in existing_foreign[name]): raise DuplicateConstraint(constraint_name)
                sql = SQL.SQL("alter table {table_name} add constraint %(constraint_name)s foreign key ({name}) references {foreign_table} on update %(on_update)s on delete %(on_delete)s" % {'constraint_name':constraint_name, 'on_update':self.change_option(on_update), 'on_delete':self.change_option(on_delete)}).format(table_name=SQL.Identifier(self.table.table_name),name=SQL.Identifier(name),foreign_table=SQL.Identifier(foreign_table.table_name))

                dtype_1 = foreign_table.sql_query.table_info.get_columns()[primary_of_other]
                dtype_2 = self.info.get_columns()[name]

                if(dtype_1!=dtype_2): raise DataTypeDifferent(primary_of_other,dtype_1,name,dtype_2)
            
                if(col_check):
        
                    try:
                        self.table.do_sql_query(cursor,sql)
                        return True

                    except psql.errors.UndefinedColumn as e:
                        get_error_info(e)
                        raise ColumnNotFound(name)

                    except psql.errors.ForeignKeyViolation as e:
                        get_error_info(e)
                        raise ForeignKeyMismatch(foreign_table.table_name,self.table.table_name,name)

                    except Exception as e:
                        get_error_info(e)
                        raise e

                    finally:
                        if(self.table.connection): self.table.connection.rollback()	

                return False

table = Table("table_1").connectToDB()
# print(table.query.table_info.table_check())
asd = SqlQuery(table)
print(asd.table_info.get_columns())
# asd.insert.insert_row({'id':2,'col1':'3'})