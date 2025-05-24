import os, sys, subprocess, traceback, requests, argparse, logging, re, functools

IS_EXE = True
APP_PATH = __file__ if (not IS_EXE) else sys.executable
CRED = {"api_key":"LbtWDu5C3yKNOEWxUNFHe5tK3viGbQJleahRHgBti9N959U5pHTH741fiaotTJaN", "secure_key":"FIkRh0D4vc7JRMgRfO2KRdauzTuYHCM98H8MlM9VKNa58hepKIgKKcIZOyALpvdB"}

def get_url(request_string: str) -> str:
    matches = re.findall(r'(https|http)//([\w.:/]+)$', request_string)
    """ Matches only the https//{--this part--}$ """
    return '://'.join(next(iter(matches))) if matches else ''

def url_join(*args):    
    return ''.join([f"{i}{(lambda x: f'/' if (x and x[-1]!='/') else '')(i)}" for i in args])

parse = argparse.ArgumentParser()
parse.add_argument("--url", type=str, help="The URL to fetch/respond data", required=True)
parse.add_argument("--exe", type=str, help="Local Path of the EXE", required=True) # Should be part of the registry and not called by Chrome URI directly
parse.add_argument( "-r", "--read", help="Specify if this is a read operation", action="store_const", const=True) # Should be part of the registry and not called by Chrome URI directly
parse.add_argument( "-w", "--write", help="Specify if this is a write operation", action="store_const", const=True) # Should be part of the registry and not called by Chrome URI directly
parse.add_argument( "-c", "--createCard", help="Specify if this is a create card operation", action="store_const", const=True) # Should be part of the registry and not called by Chrome URI directly
args = parse.parse_args()

class AttrChecker:
    ARGS = ["read", "write", "createCard"]

    @staticmethod
    def check_if_none(args: argparse.Namespace) -> bool:
        return not bool(functools.reduce(AttrChecker.or_operator,[(lambda x: x if (x is not None) else False)(getattr(args,i)) for i in AttrChecker.ARGS if (hasattr(args,i))],False))
    
    @staticmethod
    def check_if_more_than_one(args: argparse.Namespace) -> bool:
        return bool(functools.reduce(AttrChecker.add_operator,[(lambda x: x if (x is not None) else 0)(getattr(args,i)) for i in AttrChecker.ARGS if (hasattr(args,i))], 0)>1)
    
    @staticmethod
    def or_operator(a: bool, b: bool) -> bool:
        return bool(a) or bool(b)        

    @staticmethod
    def add_operator(a: int, b: int) -> int:
        return int(a) + int(b)

class Logger:
    def __init__(self, dir_path:str) -> None:
        self.log = logging.getLogger(__name__)
        file_path = os.path.join(dir_path,'app.log')
        console, file = logging.StreamHandler(), logging.FileHandler(file_path,mode="a",encoding="utf-8")
        formatter = logging.Formatter("[{asctime}]:[{levelname}]:{message}",style="{",datefmt="%d-%m-%Y %H:%M")
        console.setFormatter(formatter)
        file.setFormatter(formatter)
        self.log.addHandler(file)        
        self.log.setLevel(logging.DEBUG)
                
    def write_error(self, msg:str, type:str = "APPLICATION") -> None:
        self.log.error(msg=f"[{type}] {msg}",exc_info=True)

    def write_warning(self, msg:str, type:str = "APPLICATION") -> None:
        self.log.warning(msg=f"[{type}] {msg}")

    def write_info(self, msg:str, type:str = "APPLICATION") -> None:
        self.log.info(f"[{type}] {msg}")
    
    @staticmethod    
    def get_error_info(exception:Exception) -> str:
        if(isinstance(exception,Exception)):
            return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception}\n{''.join(traceback.format_tb(exception.__traceback__))}"
        else:
            return "Not an exception"

LOGGER = Logger(os.path.dirname(APP_PATH))

def fetch_data(url: str, creds: dict[str, str], logger: Logger) -> dict | None:
    try:
        req:requests.Response = requests.post(url, data=creds)
        json_data:dict[str, str] = req.json()
        status:int = req.status_code
        
        if(json_data and status==200):
            logger.write_info(f"Fetch of data (URL: {url}) was successful with status code: {status}", "HTTP")
            return json_data.get("data")
        else:
            logger.write_warning(f"Fetch of data (URL: {url}) was unsuccessful with status code: {status}", "HTTP")
    except Exception as e:
        logger.write_error(Logger.get_error_info(e))
        
    return None

def write_card(args:argparse.Namespace, data:str, response_url: str, creds:dict[str, str], logger: Logger) -> None:
    try:
        response = subprocess.run([args.exe, r'{"DKey1":"WriteData","DKey2":"$*E+dSuHZGnEbgA9","DKey3":"KYbuD9NpHp!KF@%t","Data":"'+data+r'","SAM":0,"SMKeyVer":1}'], capture_output=True)
        stdout, stderr, return_code = response.stdout.decode(), response.stderr.decode(), response.returncode
        
        if(return_code==0): # Everything okay
            requests.post(response_url,data={**creds,"info":"Data Write was successful","status":"true"})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            requests.post(response_url,data={**creds,"info":"Data Write was unsuccessful","status":"false"})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")

    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

def create_card(args:argparse.Namespace, data:str, response_url: str, creds:dict[str, str], logger: Logger) -> None:
    try:
        response = subprocess.run([args.exe, r'{"DKey1":"CreateCard","DKey2":"$*E+dSuHZGnEbgA9","DKey3":"KYbuD9NpHp!KF@%t","Data":"'+data+r'","SAM":0,"SMKeyVer":1}'], capture_output=True)
        stdout, stderr, return_code = response.stdout.decode(), response.stderr.decode(), response.returncode
        
        if(return_code==0): # Everything okay!
            requests.post(response_url,data={**creds,"info":"Card Creation was successful","status":"true"})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            requests.post(response_url,data={**creds,"info":"Card Creation was unsuccessful","status":"false"})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")

    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

def read_card(args:argparse.Namespace, response_url: str, creds:dict[str, str], logger: Logger) -> None:
    try:
        response = subprocess.run([args.exe, r'{"DKey1":"ReadData","DKey2":"$*E+dSuHZGnEbgA9","DKey3":"KYbuD9NpHp!KF@%t","Data":"","SAM":0,"SMKeyVer":1}'], capture_output=True)
        stdout, stderr, return_code = response.stdout.decode(), response.stderr.decode(), response.returncode
        
        data = {**creds}
        
        if(return_code==0): # Everything okay!
            data.update({"info":"Data Read was successful","status":"true","data":stdout})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            data.update({"info":"Data Read was unsuccessful","status":"false","data":stdout})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        post = requests.post(response_url,data=data)
        
        if(post.status_code==200):
            logger.write_info(f"Successful Response from URL: {response_url}, with status code: {post.status_code} and data: {post.json()}", "HTTP")
        else:
            logger.write_warning(f"Successful Response from URL: {response_url}, with status code: {post.status_code} and data: {post.json()}", "HTTP")
            
    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

LOGGER.write_info(f"Got arguments as:\n {"\n ".join([f'{i}: {getattr(args,i)}' for i in dir(args) if (i[0]!='_')])}")

if(AttrChecker.check_if_more_than_one(args)):
    LOGGER.write_warning("Please choose at most 1 flag (-r {read}, -w {write}, -c {createCard})")
    raise ValueError("Please choose at most 1 flag (-r {read}, -w {write}, -c {createCard})")

if(AttrChecker.check_if_none(args)):
    LOGGER.write_warning("Please choose 1 flag (-r {read}, -w {write}, -c {createCard})")
    raise ValueError("Please choose 1 flag (-r {read}, -w {write}, -c {createCard})")

FETCH_URL = url_join(get_url(args.url),"fetch") # URL to fetch data during write operation
RESPONSE_URL = url_join(get_url(args.url),"confirm") # URL to send confirmation during write operation
READ_URL = url_join(get_url(args.url),"read") # URL to send card data during read operation

if(args.read):
    read_card(args, READ_URL, CRED, LOGGER)

elif(args.write):
    json_data:dict[str, str] = fetch_data(FETCH_URL, CRED,LOGGER)
    
    if(json_data is not None):
        write_card(args, json_data, RESPONSE_URL, CRED, LOGGER)
    else:
        LOGGER.write_warning("No JSON data was found")

elif(args.createCard):
    json_data:dict[str, str] = fetch_data(FETCH_URL, CRED,LOGGER)

    if(json_data is not None):
        create_card(args, json_data, RESPONSE_URL, CRED, LOGGER)
    else:
        LOGGER.write_warning("No JSON data was found")
