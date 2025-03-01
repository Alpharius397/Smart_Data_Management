import os, sys, subprocess, traceback, requests, argparse, logging, re

def get_url(request_string: str) -> str:
    matches = re.findall(r'(https|http)//([\w.:/]+)$', request_string)
    """ Matches only the https://{--this part--}$ """
    return '://'.join(next(iter(matches))) if matches else ''

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

def url_join(*args):    
    return ''.join([f"{i}{(lambda x: f'/' if (x and x[-1]!='/') else '')(i)}" for i in args])

IS_EXE = True
APP_PATH = __file__ if (not IS_EXE) else sys.executable
CRED = {"api_key":"LbtWDu5C3yKNOEWxUNFHe5tK3viGbQJleahRHgBti9N959U5pHTH741fiaotTJaN", "secure_key":"FIkRh0D4vc7JRMgRfO2KRdauzTuYHCM98H8MlM9VKNa58hepKIgKKcIZOyALpvdB"}
LOGGER = Logger(os.path.dirname(APP_PATH))

parse = argparse.ArgumentParser()
parse.add_argument("--url", type=str, help="The URL to fetch/respond data", required=True)
parse.add_argument("--exe", type=str, help="Local Path of the EXE", required=True) # Should be part of the reigstry and not called by Chrome URI directly
parse.add_argument( "-r", "--read", help="Specify if this is a read operation (Note: If both read/write option are set, nothing happens)", action="store_const", const=True) # Should be part of the reigstry and not called by Chrome URI directly
parse.add_argument( "-w", "--write", help="Specify if this is a write operation (Note: If both read/write option are set, nothing happens)", action="store_const", const=True) # Should be part of the reigstry and not called by Chrome URI directly
args = parse.parse_args()

FETCH_URL = url_join(get_url(args.url),"fetch") # URL to fetch data during write operation
RESPONSE_URL = url_join(get_url(args.url),"confirm") # URL to send confirmation during write operation
READ_URL = url_join(get_url(args.url),"read") # URL to send card data during read operation

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
        stdout, stderr, return_code = response.stdout, response.stderr, response.returncode
        
        if(return_code==0): # Everything okay!
            requests.post(response_url,data={**creds,"info":"Data Write was successful","status":"true"})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            requests.post(response_url,data={**creds,"info":"Data Write was unsuccessful","status":"false"})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")

    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

def force_write_card(args:argparse.Namespace, data:str, response_url: str, creds:dict[str, str], logger: Logger) -> None:
    try:
        response = subprocess.run([args.exe, r'{"DKey1":"WriteData","DKey2":"$*E+dSuHZGnEbgA9","DKey3":"KYbuD9NpHp!KF@%t","Data":"'+data+r'","SAM":0,"SMKeyVer":1}'], capture_output=True)
        stdout, stderr, return_code = response.stdout, response.stderr, response.returncode
        
        if(return_code==0): # Everything okay!
            requests.post(response_url,data={**creds,"info":"Forecful Data Write was successful","status":"true"})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            requests.post(response_url,data={**creds,"info":"Forecful Data Write was unsuccessful","status":"false"})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")

    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

def read_card(args:argparse.Namespace, response_url: str, creds:dict[str, str], logger: Logger) -> None:
    try:
        response = subprocess.run([args.exe, r'{"DKey1":"ReadData","DKey2":"$*E+dSuHZGnEbgA9","DKey3":"KYbuD9NpHp!KF@%t","Data":"","SAM":0,"SMKeyVer":1}'], capture_output=True)
        stdout, stderr, return_code = response.stdout, response.stderr, response.returncode
        
        if(return_code==0): # Everything okay!
            requests.post(response_url,data={**creds,"info":"Data Read was successful","status":"true"})
            logger.write_info(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")
            
        else: # Something went wrong
            requests.post(response_url,data={**creds,"info":"Data Read was unsuccessful","status":"false"})
            logger.write_warning(f"Stdout: {stdout}, Stderr: {stderr}, Exitcode: {return_code}","EXE")

    except Exception as e:
        logger.write_error(Logger.get_error_info(e))

LOGGER.write_info(f"Got arguments as:\n URL: {args.url}\n EXE: {args.exe}\n READ FLAG: {args.read}\n WRITE FLAG: {args.write}")

if(args.read and args.write):
    LOGGER.write_warning("Both read and write flag cannot be true")
    raise ValueError("Both read and write flag cannot be true")

if(not (args.read or args.write)):
    LOGGER.write_warning("Both read and write flag cannot be false")
    raise ValueError("Both read and write flag cannot be false")

# Fetch Data from server
if(args.read):
    read_card(args, READ_URL, CRED, LOGGER)

elif(args.write):
    json_data:dict[str, str] = fetch_data(FETCH_URL, CRED,LOGGER)
    
    if(json_data is not None):
        write_card(args, json_data, RESPONSE_URL, CRED, LOGGER)
    else:
        LOGGER.write_warning("No JSON data was found")

