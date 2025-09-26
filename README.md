# Smart Card Utility (Go)

This Go program is a Windows-focused utility for interacting with smart cards. It provides functionality to **read, write, and create cards** via a local executable, while communicating with a remote server over HTTP.

## Key Features

- **AES-based encryption** for secure communication.  
- **Custom logging** with timestamps and error/info/warning levels.  
- **Registry integration** to register protocol handlers for read, write, and create operations.  
- **Command-line flags** to specify operations (`-r` for read, `-w` for write, `-c` for create).  
- **HTTP requests** to fetch card data and send confirmations.  
- Utilities for **URL handling, padding/unpadding, and extracting messages** from command output.

## Summary

The program automates card management while ensuring secure and traceable interactions with both the local system and remote endpoints.


## Go Development Guide

### 1. Running a Go File

1. Install Go from the [official website](https://golang.org/dl/).  
2. Run a Go file using:

```go
go run {--filename--}.go
```

### 2. Building a Go Binary for Windows
```go
GOOS=windows GOARCH=amd64 go build {--filename--}.go
```

