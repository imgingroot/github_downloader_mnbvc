#!/bin/bash

# build binaries for Linux (amd64, 386, arm7, arm64)
GOOS=linux GOARCH=amd64 go build -o gh_downloader-linux-amd64 main.go netUtils.go
GOOS=linux GOARCH=386 go build -o gh_downloader-linux-386 main.go netUtils.go
GOOS=linux GOARCH=arm GOARM=7 go build -o gh_downloader-linux-arm7 main.go netUtils.go
GOOS=linux GOARCH=arm64 go build -o gh_downloader-linux-arm64 main.go netUtils.go

# build binaries for Windows (amd64, 386)
GOOS=windows GOARCH=amd64 go build -o gh_downloader-windows-amd64.exe main.go netUtils.go
GOOS=windows GOARCH=386 go build -o gh_downloader-windows-386.exe main.go netUtils.go

# build binaries for macOS (amd64, arm64)
GOOS=darwin GOARCH=amd64 go build -o gh_downloader-darwin-amd64 main.go netUtils.go
GOOS=darwin GOARCH=arm64 go build -o gh_downloader-darwin-arm64 main.go netUtils.go

# calculate checksum for all the binaries
shasum gh_downloader-linux-amd64 > gh_downloader-linux-amd64.sha
shasum gh_downloader-linux-386 > gh_downloader-linux-386.sha
shasum gh_downloader-linux-arm7 > gh_downloader-linux-arm7.sha
shasum gh_downloader-linux-arm64 > gh_downloader-linux-arm64.sha
shasum gh_downloader-windows-amd64.exe > gh_downloader-windows-amd64.sha
shasum gh_downloader-windows-386.exe > gh_downloader-windows-386.sha
shasum gh_downloader-darwin-amd64 > gh_downloader-darwin-amd64.sha
shasum gh_downloader-darwin-arm64 > gh_downloader-darwin-arm64.sha
