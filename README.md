# gh_downloader
github仓库下载器

批量下载github仓库的工具


编译:
```
go build main.go netUtils.go
```

运行:
```
./main test.txt
```
如果不传文本文件 [test.txt](./test.txt)，默认会自动从当前目录加载txt文件作为输入（便于双击直接运行 ^_^ ）

为保证可靠，程序做了以下几点：
- 没有使用任何golang的第三方库
- 支持断点继续下载
- 拆分成1000个子目录存储下载结果
- 支持多进程下载（开几个程序就是几个进程）
- 所有的磁盘访问操作都在当前目录
- 对域名下所有ip做测试，使用速度最快的ip进行下载
- 除了codeload.github.com的代码服务器,没有任何其他网络请求


文件被下载到了当前目录的outputs目录下，日志和错误信息在logs目录

已知问题：
 - 仅下载了main或者master分支，如果仓库没有这两个分支，会下载失败

 全平台打包编译的命令（[build.sh](./build.sh)）：
```
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

```
windows下编译打包参考 [build.bat](./build.bat)
打包时，会对应的计算sha签名，生成的文件在.sha中


根据输入的文件中的 URL 列表，从 Github 上下载对应的代码库 zip 文件。它首先测试一组 IP 地址与目标域名的网络延迟，选择最快的 IP，然后逐一读取输入文件中的 URL 列表，解析 URL ，下载对应的代码库 zip 文件并保存到本地。
下载的过程中会生成日志文件和错误文件，记录下载过程中的信息和错误。代码中还定义了 log 和 erro 两个函数来分别记录正常信息和错误信息。
