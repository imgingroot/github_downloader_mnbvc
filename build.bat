set GOOS=linux
set GOARCH=amd64
go build -o gh_downloader-linux-amd64 main.go netUtils.go

set GOARCH=386
go build -o gh_downloader-linux-386 main.go netUtils.go

set GOARCH=arm GOARM=7
go build -o gh_downloader-linux-arm7 main.go netUtils.go

set GOARCH=arm64
go build -o gh_downloader-linux-arm64 main.go netUtils.go

set GOOS=windows
set GOARCH=amd64
go build -o gh_downloader-windows-amd64.exe main.go netUtils.go

set GOARCH=386
go build -o gh_downloader-windows-386.exe main.go netUtils.go

set GOOS=darwin
set GOARCH=amd64
go build -o gh_downloader-darwin-amd64 main.go netUtils.go

set GOARCH=arm64
go build -o gh_downloader-darwin-arm64 main.go netUtils.go
