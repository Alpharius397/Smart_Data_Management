from datetime import date,time

class MainException(Exception):
    """ Base Class Exception for Custom Exception """
    def __init__(self,msg:str) -> None:
        self.msg = msg
        
    def __str__(self) -> str:
        return self.msg
    
    def get_error(self) -> str:
        return str(self)

class DuplicateColumn(MainException):
    """ Exception if Duplicate Column found """
    def __init__(self, column_name:str) -> None:
        super().__init__(f"Duplicate Column Found: '{column_name}'")

class InvalidOperation(MainException):
    """ Exception if Invalid Operation Called """
    def __init__(self, op:str, valid:list|set) -> None:
        super().__init__(f"Operator Option '{op}' not found in {valid}")

class ConnectionFailed(MainException):
    """ Exception if Connection was not established """
    def __init__(self) -> None:
        super().__init__("Couldn't connect to PostgreSQL Database. Please check the credentials")

class TableNotFound(MainException):
    """ Exception if Table was not Found in Database """
    def __init__(self, table_name:str) -> None:
        super().__init__(f"Table '{table_name}' was not found in database")

class UserAutheticationFailed(MainException):
    """ Exception if User is not autheticated """
    def __init__(self,user:str) -> None:
        super().__init__(f"Password Authentication failed for user '{user}'")

class EstablishConnection(MainException):
    """ Exception if Connection was not established """
    def __init__(self) -> None:
        super().__init__(f"Attempt Connection First")

class DuplicateTable(MainException):
    """ Exception if Table is already present in Database """
    def __init__(self, table_name:str) -> None:
        super().__init__(f"Table '{table_name}' already exists")

class DataTypeNotSupported(MainException):
    """ Exception if DataType is not supported by ORM """
    def __init__(self, dtype:str, supported:list[str]) -> None:
        super().__init__(f"Data Type '{dtype}' not supported. Only these types are supported : {', '.join(supported)}.")

class ConflictingCondition(MainException):
    """ Exception if Conflicting options are selected """
    def __init__(self, col_name:str, type_1:str, type_2:str) -> None:
        super().__init__(f"Column '{col_name}' cannot be both '{type_1}' and '{type_2}' at the same time. Choose any one")

class ColumnNotFound(MainException):
    """ Exception if Column was not Found in Table """
    def __init__(self, column_name:str) -> None:
        super().__init__(f"Column '{column_name}' was not found in table")

class UnauthorizedAction(MainException):
    """ Exception if User is not autheticated to perform on table """
    def __init__(self, table_name:str, operation:str) -> None:
        super().__init__(f"User doesn't have permission on table '{table_name}' to perform '{operation}' operation")

class ColumnNotPresent(MainException):
    """ Exception if Columns (unknown column) is not present in table """
    def __init__(self) -> None:
        super().__init__(f"Some columns are not present in table")

class UniqueKeyViolation(MainException):
    """ Exception if Repeated values are found in unique-valued column """
    def __init__(self) -> None:
        super().__init__(f"Duplicate values found in columns with unique constraint")

class PrimaryKeyExists(MainException):
	""" Exception if Primary Key already exists  """
	def __init__(self, table_name:str) -> None:
		super().__init__(f"Primary Key Column already exists in table {table_name}")

class PrimaryKeyDoesNotExists(MainException):
	""" Exception if Primary Key does not exists  """
	def __init__(self, table_name:str) -> None:
		super().__init__(f"Primary Key Column does not exists in table {table_name}")

class EmptyValueDetected(MainException):
	""" Exception if any value is empty """
	def __init__(self, field:str) -> None:
		super().__init__(f"'{field}' cannot be empty")

class DataTypeMismatch(MainException):
    """ Exception if Data type is not correct for a corresponding column """    
    def __init__(self, col:str, dtype_1:tuple[str,bool], val:str | int | float | time | date | list) -> None:
        super().__init__(f"Data Type of Column {col} ({dtype_1[0]}{'[]' if dtype_1[1] else ''}) does not matches Data Type of Value '{val}'")

class ForeignKeyMismatch(MainException):
    """ Exception if some values of column in a table is not in primary key of other table """
    def __init__(self, table_1:str, table_2:str, col:str) -> None:
        super().__init__(f"Some values in column '{col}' in table '{table_2}' is not in primary key of table '{table_1}'")

class DataTypeDifferent(MainException):
    """ Exception if data types of different columns are different """
    def __init__(self, col_1:str, dtype_1:tuple[str,bool], col_2:str, dtype_2:tuple[str,bool]) -> None:
        super().__init__(f"Data Type of Column '{col_1}' ({dtype_1[0]}{'[]' if dtype_1[1] else ''}) is different from Column '{col_2}' ({dtype_2[0]}{'[]' if dtype_2[1] else ''})")

class DataConversionError(MainException):
    """ Exception if data conversion is not possible. Eg: int => array(int) """
    def __init__(self, dtype_1:str, dtype_2:str) -> None:
        super().__init__(f"Data Conversion from dtype_1 (original) '{dtype_1}' and dtype_2 (to change) '{dtype_2}' was not possible")

class ConstraintNotFound(MainException):
    """ Exception if constraint was not found in table """
    def __init__(self, constraint: str, table:str, type_of_constraint:str='') -> None:
        super().__init__(f" Constraint '{constraint}' { f'({type_of_constraint})' if type_of_constraint else ''} is not present in '{table}'")
        
class DuplicateConstraint(MainException):
    """ Exception if constraint name exists (Shouldn't happend) """
    def __init__(self, constraint_name: str) -> None:
        super().__init__(f"Constraint name '{constraint_name}' already exists")
        
class ConstraintTypeExists(MainException):
    """ Exception if constraint type (primary,foreign,unique) on column already exists """
    def __init__(self, column_name:str, constraint:str) -> None:
        super().__init__(f"Constraint of Type '{constraint}' is already present on column '{column_name}'")

class DefaultValueNotExists(MainException):
    """ Exception if Default Values is not set """
    def __init__(self, column: str) -> None:
        super().__init__(f"Column '{column}' doesn't have any default value")
        
class NullNotAccepted(MainException):
    """ Exception if column does not accepts null value """
    def __init__(self, column:str) -> None:
        super().__init__(f"Column '{column}' cannot accept null values")
        
class NullAccepted(MainException):
    """ Exception if column already accepts null values """
    def __init__(self, column:str) -> None:
        super().__init__(f"Column '{column}' accepts null values")
        
class DefaultValueExists(MainException):
    """ Exception if Default Values is set """
    def __init__(self, column: str) -> None:
        super().__init__(f"Column '{column}' have default value")
