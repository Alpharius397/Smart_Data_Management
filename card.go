package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"golang.org/x/sys/windows/registry"
	"github.com/joho/godotenv"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"regexp"
	"strings"
	"time"
)

//////////// CONSTANTS ////////////
var aes_key_1 string = os.Getenv("AES_KEY_1") // keep them same as the django AES KEYS
var aes_key_2 string = os.Getenv("AES_KEY_2")
const aes_iv_length int = 16

//////////// TYPES ////////////

type Logger struct {
	logger *log.Logger
}

func (l Logger) SetPrefix() Logger {
	l.logger.SetPrefix(time.Now().Format("[2-01-2006 15:04:05]:"))
	return l
}

func (l Logger) WriteError(what string, e error) {
	l.logger.Printf("[ERROR]:[%s] %s", what, e)
}

func (l Logger) WriteInfo(what string, e string) {
	l.logger.Printf("[INFO]:[%s] %s", what, e)
}

func (l Logger) WriteWarning(what string, e string) {
	l.logger.Printf("[WARNING]:[%s] %s", what, e)
}

type CardArgs struct {
	DKey1    string
	DKey2    string
	DKey3    string
	Data     string
	SAM      int
	SMKeyVer int
}

// Loads default arguments for card exe
func (c CardArgs) LoadCreds(what string, data string) CardArgs {
	c.DKey1 = what
	c.DKey2 = os.Getenv("DKey2")
	c.DKey3 = os.Getenv("DKey3")
	c.Data = data
	c.SAM = 0
	c.SMKeyVer = 1

	return c
}

type FetchJson struct {
	Data string `json:"data"`
}

func readJson(message string, status bool, card string, data string) map[string]string {
	return map[string]string{"message": message, "status": boolToString(status), "card": card, "data": data}
}

func confirmJson(message string, status bool, card string) map[string]string {
	return map[string]string{"message": message, "status": boolToString(status), "card": card}
}

//////////// CRYPTO UTILS ////////////

func aesEncrypt(ciphertext *[]byte, plaintext []byte, key string, iv *[]byte) {

	block, err := aes.NewCipher([]byte(key))

	if err != nil {
		panic(err)
	}

	mode := cipher.NewCBCEncrypter(block, *iv)

	mode.CryptBlocks(*ciphertext, plaintext)
}

func aesDecrypt(plaintext *[]byte, ciphertext []byte, key string, iv *[]byte) {

	block, err := aes.NewCipher([]byte(key))
	mode := cipher.NewCBCDecrypter(block, *iv)

	if err != nil {
		panic(err)
	}

	mode.CryptBlocks(*plaintext, ciphertext)

}

func pad(data *[]byte, blockSize int) {

	paddingLength := blockSize - (len(*data) % (blockSize))

	lastSlice := make([]byte, 0)
	for i := 0; i < paddingLength; i++ {
		lastSlice = append(lastSlice, byte(paddingLength))
	}

	*data = append(*data, lastSlice...)
}

func unpad(data *[]byte, blockSize int) {
	padLength := int((*data)[len(*data)-1])

	if (padLength < 1) || (padLength > min(blockSize, padLength)) {
		panic(errors.New("Incorrect padding length"))
	}

	lastSlice := make([]byte, 0)
	for i := 0; i < padLength; i++ {
		lastSlice = append(lastSlice, byte(padLength))
	}

	if string((*data)[(len(*data)-padLength):len(*data)]) != string(lastSlice) {
		panic(errors.New("Incorrect padding found"))
	}

	*data = (*data)[:(len(*data) - padLength)]
}

func getAuthKey() string {
	adding5minutes := time.Duration(5) * time.Minute
	date := []byte(time.Now().Add(adding5minutes).Format("15:04:02:01:2006"))

	iv := make([]byte, aes.BlockSize)
	_, err := rand.Read(iv)

	if err != nil {
		panic(err)
	}

	pad(&date, aes.BlockSize)
	token := make([]byte, len(date))

	aesEncrypt(&token, date, aes_key_1, &iv)
	aesEncrypt(&token, token, aes_key_2, &iv)

	iv = append(iv, token...)
	pad(&iv, 3)
	return base64.URLEncoding.EncodeToString(iv)
}

// Sample function to decode data
// func getDateTime(data string) string {

// 	encrypted, err := base64.URLEncoding.DecodeString(data)
// 	unpad(&encrypted, 3)

// 	if err != nil {
// 		panic(err)
// 	}

// 	iv := encrypted[:aes_iv_length]
// 	ciphertext := encrypted[aes_iv_length:]

// 	token := make([]byte, len(ciphertext))

// 	aesDecrypt(&token, ciphertext, aes_key_2, &iv)
// 	aesDecrypt(&token, token, aes_key_1, &iv)

// 	unpad(&token, aes.BlockSize)

// 	return string(token)

// }

//////////// RE UTILS ////////////

// Extracts general message from stdOut. true -> pattern found, else false
func extractMsg(s string) (string, bool) {
	re := regexp.MustCompile(`:(\s*)(?<data>([[:graph:]\s]+))(\s*)$`)

	matches := re.FindStringSubmatch(s)

	if matches == nil || s == "" {
		return "Pattern Not Found", false
	}

	return strings.TrimSpace(matches[re.SubexpIndex("data")]), true
}

// Get the url from the args
func get_url(s string) (string, error) {
	re := regexp.MustCompile("(?P<proto>https|http)//(?P<url>[a-zA-Z0-9+-_.:/]+)$")
	matches := re.FindStringSubmatch(s)

	if matches == nil || s == "" {
		return "", errors.New("Empty String")
	}

	return matches[re.SubexpIndex("proto")] + "://" + matches[re.SubexpIndex("url")], nil
}

//////////// GENERAL UTILS ////////////

func mapAndJoin(s []string, sep string) string {
	for i, _ := range s {
		s[i] = strings.TrimRight(s[i], sep)
	}

	return strings.Join(s, sep) + sep
}

func boolToString(value bool) string {
	switch value {
		case true:
			return "true"
		case false:
			return "false"
		default:
			return "none"
	}
}

//////////// WINDOWS UTILS ////////////

func windows_url_join(args ...string) string {
	return mapAndJoin(args, "\\")
}

func get_last_windows(args string) string {
	args = strings.TrimRight(args, "\\")
	rightIndex := strings.LastIndex(args, "\\")
	return args[:rightIndex+1]
}

//////////// URL UTILS ////////////

// Helper Function to Join URLs
func url_join(args ...string) string {
	return mapAndJoin(args, "/")
}

func setUrlValue(memo map[string]string) url.Values {
	f := url.Values{}

	for key, val := range memo {
		f.Set(key, val)
	}

	return f
}

//////////// HTTP UTILS ////////////

func baseRequest(method string, url string, body url.Values) (*http.Response, error) {

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
func makeResponsePOST(response_url string, f url.Values) error {
	_, err := baseRequest("POST", response_url, f)
	return err
}

func makeFetchPOST(request_url string) (FetchJson, error) {
	data := FetchJson{}

	resp, err := baseRequest("POST", request_url, url.Values{})

	if err != nil {
		return data, err
	}

	if resp.StatusCode != 200 {
		return data, errors.New(fmt.Sprintf("URL Response from url: \"%s\" was unsuccessful with status code: \"%d\"", request_url, resp.StatusCode))
	}

	body, err := io.ReadAll(resp.Body)
	defer resp.Body.Close()

	if err != nil {
		return data, err
	}

	err = json.Unmarshal(body, &data)

	return data, err
}

func FetchUrl(request_url string, log Logger) (FetchJson, error) {

	data, err := makeFetchPOST(request_url)

	if err != nil {
		log.WriteError("HTTP", err)
	} else {
		log.WriteInfo("HTTP", fmt.Sprintf("Data Fetch from url: \"%s\" was successful with status code: \"200\"", request_url))
	}

	return data, err
}

//////////// CARD UTILS ////////////

// Get Card ID
func GetCardID(exe_path string, log Logger) (id string, err error) {

	var out strings.Builder
	var errStd strings.Builder
	var cardError error = nil

	args, err := json.Marshal(CardArgs{}.LoadCreds("GetID", ""))

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return "", err
	}

	cmd := exec.Command(exe_path, string(args))
	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	if errStd.String() != "" || out.String() == "" {

		log.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%#v\"", exe_path, string(args), err)))

		return id, err

	} else {

		log.WriteInfo("EXE", fmt.Sprintf("Exe was executed successfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))

		data, ok := extractMsg(out.String())
		id = data

		if !ok {
			cardError = errors.New("Failed to retrieve Card ID")
		}

		return id, cardError
	}
}

func WriteCard(exe_path string, data string, response_url string, log Logger) {

	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	args, err := json.Marshal(CardArgs{}.LoadCreds("WriteData", data))

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path, string(args))
	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	cardID, err := GetCardID(exe_path, log)

	if err != nil {
		httpError = makeResponsePOST(response_url, setUrlValue(confirmJson(err.Error(), false, "")))
		return
	}

	if out.String() == "" || errStd.String() != "" {
		log.WriteInfo("EXE", fmt.Sprintf("Exe was executed unsuccessfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))
		errorTxt, found := extractMsg(errStd.String())

		var msg strings.Builder

		msg.WriteString("Card Write was unsuccessful")

		if found {
			msg.WriteString(fmt.Sprintf(" (%s)", errorTxt))
		}

		httpError = makeResponsePOST(response_url, setUrlValue(confirmJson(msg.String(), false, "")))

	} else {
		log.WriteInfo("EXE", fmt.Sprintf("Exe was executed successfully. Stdout: \"%s\", Stderr: \"%s\"", out.String(), errStd.String()))
		httpError = makeResponsePOST(response_url, setUrlValue(confirmJson("Card Write was successful", true, cardID)))
	}

	if httpError != nil {
		log.WriteError("HTTP", httpError)
	} else {
		log.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully", response_url))
	}
}

func ReadCard(exe_path string, response_url string, log Logger) {

	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	args, err := json.Marshal(CardArgs{}.LoadCreds("ReadData", ""))

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path, string(args))
	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	cardID, err := GetCardID(exe_path, log)

	if err != nil {
		httpError = makeResponsePOST(response_url, setUrlValue(readJson(err.Error(), false, "", "")))
		return
	}

	err = cmd.Run()

	if out.String() == "" || errStd.String() != "" {
		log.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%#v\"", exe_path, string(args), err)))
		httpError = makeResponsePOST(response_url, setUrlValue(readJson("Card Read was unsuccessful", false, cardID, "")))

	} else {
		log.WriteInfo("EXE", fmt.Sprintf("Exe was executed successfully. Args: \"%s\".Stdout: \"%s\", Stderr: \"%s\"", string(args), out.String(), errStd.String()))
		data, ok := extractMsg(out.String())

		if ok {
			httpError = makeResponsePOST(response_url, setUrlValue(readJson("Card Read was successful", true, cardID, data)))
		} else {
			httpError = makeResponsePOST(response_url, setUrlValue(readJson("Failed to retrieve data from card", false, cardID, data)))
		}
	}

	if httpError != nil {
		log.WriteError("HTTP", httpError)
	} else {
		log.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully", response_url))
	}
}

func CreateCard(exe_path string, data string, response_url string, log Logger) {

	var out strings.Builder
	var errStd strings.Builder
	var httpError error

	args, err := json.Marshal(CardArgs{}.LoadCreds("CreateCard", ""))

	if err != nil {
		log.WriteError("ARGS", errors.New(fmt.Sprintf("Parsing Args to JSON failed. Error: \"%s\"", err)))
		return
	}

	cmd := exec.Command(exe_path, string(args))
	cmd.Stdout = &out
	cmd.Stderr = &errStd
	cmd.Dir = get_last_windows(exe_path)

	err = cmd.Run()

	cardID, err := GetCardID(exe_path, log)

	if err != nil {
		httpError = makeResponsePOST(response_url, setUrlValue(readJson(err.Error(), false, "", "")))
		return
	}

	if out.String() == "" || errStd.String() != "" {
		log.WriteError("EXE", errors.New(fmt.Sprintf("Failed to run the exe \"%s\". Args: %s. Error: \"%#v\"", exe_path, string(args), err)))
		httpError = makeResponsePOST(response_url, setUrlValue(readJson("Card Creation was unsuccessful", false, cardID, "")))

	} else {
		log.WriteInfo("EXE", fmt.Sprintf("Exe was executed successfully. Args: \"%s\".Stdout: \"%s\", Stderr: \"%s\"", string(args), out.String(), errStd.String()))
		httpError = makeResponsePOST(response_url, setUrlValue(readJson("Card Creation was successful", true, cardID, data)))
	}

	if httpError != nil {
		log.WriteError("HTTP", httpError)
	} else {
		log.WriteInfo("HTTP", fmt.Sprintf("Response to url: \"%s\" was send successfully", response_url))
	}
}

//////////// REGISTRY UTILS ////////////

func writeProtocol(filePath string) error {

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

	command := fmt.Sprintf("\"%s\" \"--url=%%1\" \"--log=%s\" \"--exe=%s\" \"-w\"", filePath, strings.TrimRight(windows_url_join(get_last_windows(filePath), "app.log"), "\\"), strings.TrimRight(windows_url_join(get_last_windows(filePath), "SmartCardSolutions", "SmartCardSolutions.exe"), "\\"))
	err = cmdKey.SetStringValue("", command)

	if err != nil {
		return fmt.Errorf("Failed to set command: %v", err)
	}

	return nil
}

func readProtocol(filePath string) error {

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

	command := fmt.Sprintf("\"%s\" \"--url=%%1\" \"--log=%s\" \"--exe=%s\" \"-r\"", filePath, strings.TrimRight(windows_url_join(get_last_windows(filePath), "app.log"), "\\"), strings.TrimRight(windows_url_join(get_last_windows(filePath), "SmartCardSolutions", "SmartCardSolutions.exe"), "\\"))
	err = cmdKey.SetStringValue("", command)

	if err != nil {
		return fmt.Errorf("Failed to set command: %v", err)
	}

	return nil
}

func createProtocol(filePath string) error {

	createProto := "createExe"

	key, _, err := registry.CreateKey(registry.CLASSES_ROOT, createProto, registry.ALL_ACCESS)

	if err != nil {
		return fmt.Errorf("Failed to create registry key: %v", err)
	}

	defer key.Close()

	_ = key.SetStringValue("URL Protocol", "")

	cmdKeyPath := windows_url_join(createProto, "shell", "open", "command")

	cmdKey, _, err := registry.CreateKey(registry.CLASSES_ROOT, cmdKeyPath, registry.ALL_ACCESS)

	if err != nil {
		return fmt.Errorf("Failed to create command key: %v", err)
	}

	defer cmdKey.Close()

	command := fmt.Sprintf("\"%s\" \"--url=%%1\" \"--log=%s\" \"--exe=%s\" \"-c\"", filePath, strings.TrimRight(windows_url_join(get_last_windows(filePath), "app.log"), "\\"), strings.TrimRight(windows_url_join(get_last_windows(filePath), "SmartCardSolutions", "SmartCardSolutions.exe"), "\\"))
	err = cmdKey.SetStringValue("", command)

	if err != nil {
		return fmt.Errorf("Failed to set command: %v", err)
	}

	return nil
}

func main() {

	godotenv.Load() // Note: This is a placeholder, replace os.GetEnv with corresponding env variables

	if len(os.Args[1:]) == 0 {

		fileName, err := os.Executable()
		logFile, err := os.OpenFile(strings.TrimRight(windows_url_join(get_last_windows(fileName), "app.log"), "\\"), os.O_APPEND|os.O_CREATE|os.O_RDWR, 0666)

		if err != nil {
			log.Fatalf("Error: %s", err)
		}

		Log := log.New(logFile, "", log.Lmsgprefix)
		logger := Logger{logger: Log}.SetPrefix()

		defer logFile.Close()

		defer func() {

			r := recover()

			if r != nil {
				error_string := fmt.Sprintf("%+v\n", r)
				logger.WriteError("PANIC", errors.New(error_string))
			}
		}()

		err = readProtocol(fileName)

		if err != nil {
			logger.WriteError("ReadExe", err)
		}

		err = writeProtocol(fileName)

		if err != nil {
			logger.WriteError("WriteExe", err)
		}

		err = createProtocol(fileName)

		if err != nil {
			logger.WriteError("CreateExe", err)
		}

		logger.WriteInfo("Registry", "Registry Updated!")

	} else {

		fs := flag.NewFlagSet("card", flag.ContinueOnError)
		fs.SetOutput(os.Stdout)

		url := fs.String("url", "sampleURL", "`URL` Path to send requests or receive setUrlValue")
		exe := fs.String("exe", "sampleExePath", "`Exe` Local Path of the EXE")
		logPath := fs.String("log", "sampleLogPath", "`Log` Local Path of the LogFile")
		read := fs.Bool("r", false, "`readCard` Flag to specify if this is a read operation")
		write := fs.Bool("w", false, "`writeCard` Flag to specify if this is a write operation")
		create := fs.Bool("c", false, "`createCard` Flag to specify if this is a create operation")
		err := fs.Parse(os.Args[1:])

		if err != nil {
			log.Fatalf("Parsing Error: %s", err)
		}

		logFile, err := os.OpenFile(*logPath, os.O_APPEND|os.O_CREATE|os.O_RDWR, 0666)

		if err != nil {
			log.Fatalf("Failed to find file: %s", *logPath)
		}

		defer logFile.Close()

		Log := log.New(logFile, "", log.Lmsgprefix)
		logger := Logger{logger: Log}.SetPrefix()

		defer func() {

			r := recover()

			if r != nil {
				error_string := fmt.Sprintf("%+v\n", r)
				logger.WriteError("Panic occurred", errors.New(error_string))
			}
		}()

		if *read && *write && *create {
			logger.WriteWarning("APPLICATION", "Please choose at most 1 flag (-r {read}, -w {write}, -c {createCard})")

		} else if !(*read) && !(*write) && !(*create) {
			logger.WriteWarning("APPLICATION", "Please choose 1 flag (-r {read}, -w {write}, -c {createCard})")

		} else {

			if *read {

				Url, err := get_url(*url)

				if err != nil {
					logger.WriteError("APPLICATION", err)
				}

				readURL := url_join(Url)
				ReadCard(*exe, readURL, logger)

			} else if *write {
				Url, err := get_url(*url)

				if err != nil {
					logger.WriteError("APPLICATION", err)
				}

				fetchURL := url_join(Url, "fetch")
				confirmURL := url_join(Url, "confirm")

				data, err := FetchUrl(fetchURL, logger)

				if err != nil {
					logger.WriteError("HTTP", err)
				} else {
					WriteCard(*exe, data.Data, confirmURL, logger)
				}

			} else if *create {
				Url, err := get_url(*url)

				if err != nil {
					logger.WriteError("APPLICATION", err)
				}

				fetchURL := url_join(Url, "fetch")
				confirmURL := url_join(Url, "confirm")

				data, err := FetchUrl(fetchURL, logger)

				if err != nil {
					logger.WriteError("HTTP", err)
				} else {
					CreateCard(*exe, data.Data, confirmURL, logger)
				}
			}
		}
	}
}
