package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"regexp"
	"strings"
	"time"
	"golang.org/x/sys/windows/registry"
)

const api_key string = "LbtWDu5C3yKNOEWxUNFHe5tK3viGbQJleahRHgBti9N959U5pHTH741fiaotTJaN"
const secret_key string = "FIkRh0D4vc7JRMgRfO2KRdauzTuYHCM98H8MlM9VKNa58hepKIgKKcIZOyALpvdB"

func getAuthKey() string {
	date := time.Now().Format("15:02:01:2006")
	h := sha256.New()
	h.Write([]byte(date))
	h.Write([]byte(api_key))
	h.Write([]byte(secret_key))
	return hex.EncodeToString(h.Sum(nil))
}

func extractMsg(s string) (string, bool) {
	re := regexp.MustCompile(`:(\s*)(?<data>([a-zA-Z0-9\s:=+/]+))(\s*)$`)

	matches := re.FindStringSubmatch(s)

	if matches==nil {
		return "Pattern Not Found", false
	}

	return strings.TrimSpace(matches[re.SubexpIndex("data")]) , true
}

// Get the url from the args
func get_url(s string) (string, error) {
	re := regexp.MustCompile("(?P<proto>https|http)//(?P<url>[a-zA-Z0-9.:/]+)$")
	matches := re.FindStringSubmatch(s)

	if(matches==nil || s==""){
		return "", errors.New("Empty String")
	}

	return matches[re.SubexpIndex("proto")] + "://" + matches[re.SubexpIndex("url")], nil
}

// Helper Function to Join URLs
func url_join(args ...string) (string){
	var url string = ""

	for _, i := range(args){
		url += i

		if(i[len(i)-1]!='/'){
			url += "/"
		}
	}

	return url
}

func windows_url_join(args ...string) (string){
	var url string = ""

	for idx, i := range(args){
		url += i

		if(len(args)-1==idx){ 
			break
		}

		if url[len(url)-1] == '\\' {
			continue
		}
		url += "\\"
	}

	return url
}

func get_last_windows(args string) (string){
	str := strings.Split(args, "\\")
	var url string = ""

	for i, v := range(str) {
		if(i==len(str)-1){ 
			break
		}
		url += v+"\\"
	}

	return url
}

type Logger struct{
	logger *log.Logger
}

func (l Logger) SetPrefix() Logger {
	l.logger.SetPrefix(time.Now().Format("[2-01-2006 15:04:05]:"))
	return l
}

func (l Logger) WriteError(what string,e error){
	l.logger.Printf("[ERROR]:[%s] %s",what,e)
}

func (l Logger) WriteInfo(what string,e string){
	l.logger.Printf("[INFO]:[%s] %s",what,e)
}

func (l Logger) WriteWarning(what string,e string){
	l.logger.Printf("[WARNING]:[%s] %s",what,e)
}

type FetchJson struct{
	Data string   `json:"data"`
	Errors string `json:"error"`
}

type CardArgs struct{
	DKey1 string 
	DKey2 string
	DKey3 string
	Data string
	SAM int
	SMKeyVer int 
}

// Loads default arguments for card exe 
func (c CardArgs) LoadCreds(what string, data string) CardArgs {
	c.DKey1 = what
	c.DKey2 = "$*E+dSuHZGnEbgA9"
	c.DKey3 = "KYbuD9NpHp!KF@%t"
	c.Data = data
	c.SAM = 0
	c.SMKeyVer = 1

	return c
}

func CREDS() url.Values {
	f:=url.Values{}

	f.Set("api_key",getAuthKey())
	
	return f
}

func Response(memo map[string] string) url.Values {
	f:=url.Values{}

	f.Set("api_key",getAuthKey())

	for key,val := range(memo){
		f.Set(key, val)
	}

	return f
}

func makeFetchPOST(request_url string, f url.Values) (FetchJson, error){
	data := FetchJson{}

	resp, err := __Request("POST", request_url, f)

	if err != nil {
		return data, err
	}

	if resp.StatusCode != 200 {
		return data, errors.New(fmt.Sprintf("URL Response from url: \"%s\" was unsuccessful with status code: \"%d\"",request_url, resp.StatusCode))
	}
	
	body, err := io.ReadAll(resp.Body)
	defer resp.Body.Close()

	if err != nil {
		return data, err
	}
	
	err = json.Unmarshal(body, &data)
	
	return data, err
}

func __Request(method string, url string ,body url.Values) (*http.Response, error) {

	request, err := http.NewRequest(method, url, strings.NewReader(body.Encode()))

	if err != nil {
		return nil, err
	}

	var authBearer strings.Builder

	authBearer.WriteString("Bearer ")
	authBearer.WriteString(getAuthKey())

	request.Header.Add("Authorization", authBearer.String())
	request.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := http.DefaultClient.Do(request)

	if err != nil {
		return nil, err
	}

	return resp, nil
}

// One Way Request
func makeResponsePOST(response_url string, f url.Values) (error){	
	_, err := __Request("POST", response_url, f)
	return err
}

func FetchUrl(request_url string, log Logger) (FetchJson) {
	
	data, err := makeFetchPOST(request_url, CREDS())

	if err != nil {
		log.WriteError("HTTP", err)
	} else{
		log.WriteInfo("HTTP", fmt.Sprintf("Data Fetch from url: \"%s\" was successful with status code: \"200\"",request_url))
	}

	return data
}

func GetCardID(exe_path string, log Logger) (id string, err error) {
	args, err := json.Marshal(CardArgs{}.LoadCreds("GetID",""))

	res := "Null"

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return res, err
	}

	cmd := exec.Command(exe_path, string(args))
	var out strings.Builder
	var errStd strings.Builder
	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	if (errStd.String()!="" || out.String()=="") {
		log.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%s\"", exe_path, string(args), err)))
		return id, err

	} else {

		var cardError error = nil

		log.WriteInfo("EXE",fmt.Sprintf("Exe was executed successfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))
		
		data, ok := extractMsg(out.String())
		id = data

		if(!ok){
			cardError = errors.New("Failed to retrieve Card ID")
		}

		return id, cardError
	}
}

func WriteCard(exe_path string, data string, response_url string, log Logger) {

	args, err := json.Marshal(CardArgs{}.LoadCreds("WriteData",data))

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path, string(args))
	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	cardID, err := GetCardID(exe_path, log)

	if err!=nil {
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Card Creation was unsuccessful","status":"false"}))
		return
	}
	
	if(out.String()=="" || errStd.String()!=""){
		log.WriteInfo("EXE",fmt.Sprintf("Exe was executed unsuccessfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Card Creation was unsuccessful","status":"false"}))
		
	} else {
		log.WriteInfo("EXE",fmt.Sprintf("Exe was executed successfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Card Creation was successful","status":"true","cardID":cardID}))
	}

	
	if httpError != nil {
		log.WriteError("HTTP", httpError)
	} else {
		log.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully",response_url))
	}
}

func ReadCard(exe_path string, response_url string, logger Logger) {

	args, err := json.Marshal(CardArgs{}.LoadCreds("ReadData", ""))

	if err != nil {
		logger.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path,string(args))
	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	if (out.String()=="" || errStd.String()!="") {
		logger.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%s\"", exe_path, string(args), err)))
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Data Read was unsuccessful","status":"false"}))
	
	} else {
		logger.WriteInfo("EXE",fmt.Sprintf("Exe was executed successfully. Args: \"%s\".Stdout: \"%s\", Stderr: \"%s\"", string(args), out.String(), errStd.String()))
		data, _ := extractMsg(out.String())
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Data Read was successful","status":"true","data":data}))
	}

	if httpError != nil {
		logger.WriteError("HTTP", httpError)
	} else {
		logger.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully",response_url))
	}
}

func CreateCard(exe_path string, data string, response_url string, logger Logger) {

	args, err := json.Marshal(CardArgs{}.LoadCreds("CreateCard", ""))

	if err != nil {
		logger.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path, string(args))
	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	if (out.String()=="" || errStd.String()!="") {
		logger.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%s\"", exe_path, string(args), err)))
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Data Read was unsuccessful","status":"false"}))
	
	} else {
		logger.WriteInfo("EXE",fmt.Sprintf("Exe was executed successfully. Args: \"%s\".Stdout: \"%s\", Stderr: \"%s\"", string(args), out.String(), errStd.String()))
		httpError = makeResponsePOST(response_url, Response(map[string]string{"info":"Data Read was successful","status":"true","data":out.String()}))
	}
	
	if httpError != nil {
		logger.WriteError("HTTP", httpError)
	} else {
		logger.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully",response_url))
	}
}

func writeProtocol(filePath string) (error) {

	writeProto := "writeExe"

	key, _, err := registry.CreateKey(registry.CLASSES_ROOT, writeProto, registry.ALL_ACCESS)
	if err != nil {
		return fmt.Errorf("Failed to create registry key: %v", err)
	}
	defer key.Close()

	_ = key.SetStringValue("URL Protocol", "")

	cmdKeyPath := windows_url_join(writeProto, "shell", "open", "command")

	cmdKey, _, err := registry.CreateKey(registry.CLASSES_ROOT, cmdKeyPath, registry.ALL_ACCESS)

	if err != nil {
		return fmt.Errorf("Failed to create command key: %v", err)
	}
	
	defer cmdKey.Close()

	command := fmt.Sprintf("\"%s\" \"--url=%%1\" \"--log=%s\" \"--exe=%s\" \"-w\"", filePath, windows_url_join(get_last_windows(filePath),"app.log"), windows_url_join(get_last_windows(filePath), "SmartCardSolutions", "SmartCardSolutions.exe"))
	err = cmdKey.SetStringValue("", command)

	if err != nil {
		return fmt.Errorf("Failed to set command: %v", err)
	}

	return nil
}

func readProtocol(filePath string) (error) {

	readProto := "readExe"

	key, _, err := registry.CreateKey(registry.CLASSES_ROOT, readProto, registry.ALL_ACCESS)
	if err != nil {
		return fmt.Errorf("Failed to create registry key: %v", err)
	}
	defer key.Close()

	_ = key.SetStringValue("URL Protocol", "")

	cmdKeyPath := windows_url_join(readProto, "shell", "open", "command")

	cmdKey, _, err := registry.CreateKey(registry.CLASSES_ROOT, cmdKeyPath, registry.ALL_ACCESS)

	if err != nil {
		return fmt.Errorf("Failed to create command key: %v", err)
	}
	
	defer cmdKey.Close()

	command := fmt.Sprintf("\"%s\" \"--url=%%1\" \"--log=%s\" \"--exe=%s\" \"-r\"", filePath, windows_url_join(get_last_windows(filePath),"app.log"), windows_url_join("SmartCardSolutions", "SmartCardSolutions.exe"))
	err = cmdKey.SetStringValue("", command)

	if err != nil {
		return fmt.Errorf("Failed to set command: %v", err)
	}

	return nil
}

func main(){

	if len(os.Args[1:]) == 0 {

		fileName, err := os.Executable()

		if err != nil {
			log.Fatalf("Error: %s", err)
		}

		err = readProtocol(fileName)
		if err != nil {
			log.Fatalf("Failed to set readExe protocol: %v", err)
		}

		err = writeProtocol(fileName)
		if err != nil {
			log.Fatalf("Failed to writeExe protocol: %v", err)
		}
		fmt.Printf("Registry Updated!")
		return
	}
	
	fs := flag.NewFlagSet("card", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	url := fs.String("url", "sampleURL", "`URL` Path to send requests or receive response")
	exe := fs.String("exe", "sampleExePath", "`Exe` Local Path of the EXE")
	logPath := fs.String("log", "sampleLogPath", "`Log` Local Path of the LogFile")
	read := fs.Bool("r", false, "`readCard` Flag to specify if this is a read operation")
	write := fs.Bool("w", false, "`writeCard` Flag to specify if this is a write operation")
	create := fs.Bool("c", false, "`createCard` Flag to specify if this is a create operation")
	err := fs.Parse(os.Args[1:])

	if err !=nil {
		log.Fatalf("Parsing Error: %s", err)
	}

	logFile, err := os.OpenFile(*logPath, os.O_APPEND|os.O_CREATE|os.O_RDWR, 0666)

	if err != nil {
		log.Fatalf("Failed to find file: %s",*logPath)
	}

	defer logFile.Close()

	Log := log.New(logFile,"",log.Lmsgprefix)
	logger := Logger{logger: Log}.SetPrefix()


	if *read && *write && *create {
		logger.WriteWarning("APPLICATION", "Please choose at most 1 flag (-r {read}, -w {write}, -c {createCard})")
	} else if (!(*read) && !(*write) && !(*create)) {
		logger.WriteWarning("APPLICATION", "Please choose 1 flag (-r {read}, -w {write}, -c {createCard})")
	} else {

		if *read {

			Url, err := get_url(*url)

			if err != nil {
				logger.WriteError("APPLICATION", err)
			}

			readURL := url_join(Url,"read")
			ReadCard(*exe, readURL, logger)
			
		} else if (*write){
			Url, err := get_url(*url)

			if err != nil {
				logger.WriteError("APPLICATION", err)
			}

			fetchURL := url_join(Url,"fetch")
			confirmURL := url_join(Url,"confirm")

			data := FetchUrl(fetchURL, logger)

			if err != nil {
				logger.WriteError("HTTP", err)
			}

			WriteCard(*exe, data.Data, confirmURL, logger)

		} else if (*create){
			Url, err := get_url(*url)

			if err != nil {
				logger.WriteError("APPLICATION", err)
			}

			fetchURL := url_join(Url,"fetch")
			confirmURL := url_join(Url,"confirm")

			data := FetchUrl(fetchURL, logger)

			if err != nil {
				logger.WriteError("HTTP", err)
			}

			CreateCard(*exe, data.Data, confirmURL, logger)
		}
	}

}

