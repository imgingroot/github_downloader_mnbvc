// 从文本文件中逐行读取，每行的内容为 编号,地址
// 其中地址的格式类似于 https://github.com/作者/名字.git 把其中的编号，作者，名字，都提取出来
// 用作者和名字拼成一个新的url，调用download方法进行下载，download方法接受2个参数，url和目标路径，返回值不为nil说明下载成功，download方法暂时不用实现。
// 目标路径为 编号.downloading ，在下载完成以后，把文件移动到最终路径，最终路径为 编号后3位+/+编号.zip，在下载前，如果最终路径目录不存在则新建，如果文件已经存在则跳过这次下载

package main

import (
	"bufio"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/imgingroot/httpIPdownloader"
)

func main() {

	ips := []string{"20.205.243.165", "199.59.148.9", "20.27.177.114", "192.30.255.121", "140.82.121.9", "140.82.121.10", "140.82.112.10", "140.82.113.9", "140.82.112.9", "140.82.114.10", "20.200.245.246", "140.82.113.10", "20.248.137.55", "20.207.73.88"}
	domain := "codeload.github.com"

	fmt.Println("开始测速...")

	fastestIP, spds, err := testDomainIPs(domain, ips)
	if err != nil {
		fmt.Println(err)
		return
	}
	for _, s := range spds {
		fmt.Printf("ip: %s\t --> %d ms \t[%v]\n", s.ip, s.speed, s.isConnected)
	}

	args := os.Args[1:]
	if len(args) == 0 {
		files, err := filepath.Glob("*.txt")
		if err != nil {
			panic(err)
		}
		if len(files) == 0 {
			fmt.Println("Usage: go run main.go <input_file> . No txt files found in current directory")
			return
		}

		args = files[:1]
	}

	filename := args[0]
	fmt.Println("Processing file:", filename)

	// 打开待处理文件
	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	err = os.MkdirAll("logs", os.ModePerm)
	err = os.MkdirAll("output", os.ModePerm)
	if err != nil {
		panic(err)
	}

	// 新建日志文件和错误文件，以当前时间为基准
	t := time.Now().Format("2006-01-02-15-04-05")
	logFile, err := os.Create(fmt.Sprintf("logs/download-%s.log", t))
	if err != nil {
		panic(err)
	}
	defer logFile.Close()

	errFile, err := os.Create(fmt.Sprintf("logs/errors-%s.log", t))
	if err != nil {
		panic(err)
	}
	defer errFile.Close()

	// 定义 log 函数记录日志信息
	log := func(format string, args ...interface{}) {
		msg := fmt.Sprintf(format, args...)
		now := time.Now().Format("2006-01-02 15:04:05")
		fmt.Printf("[%s] %s", now, msg)
		fmt.Fprintf(logFile, "[%s] %s", now, msg)
	}

	// 定义 error 函数记录错误信息
	erro := func(format string, args ...interface{}) {
		msg := fmt.Sprintf(format, args...)
		now := time.Now().Format("2006-01-02 15:04:05")
		fmt.Fprintf(os.Stderr, "[%s] [ERROR] %s", now, msg)
		fmt.Fprintf(errFile, "[%s] %s", now, msg)
	}

	// 逐行读取文件
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()

		// 解析行数据
		parts := strings.Split(line, ",")
		id := parts[0]
		addr := strings.Trim(parts[1], " ")

		// 解析地址
		u, err := url.Parse(addr)
		if err != nil {
			erro("Error parsing URL: %s ID= %s \n", err, id)
			continue
		}
		pathParts := strings.Split(u.Path, "/")
		if len(pathParts) < 3 {
			erro("Invalid URL: %s  ID= %s \n", addr, id)
			continue
		}
		author := pathParts[1]
		name := pathParts[2][:len(pathParts[2])-4]

		// 拼接 URL 并下载文件https://github.com/imgingroot/httpIPdownloader/archive/refs/heads/main.zip
		url := fmt.Sprintf("https://codeload.github.com/%s/%s/zip/refs/heads/main", author, name)
		url2 := fmt.Sprintf("https://codeload.github.com/%s/%s/zip/refs/heads/master", author, name)
		targetPath := fmt.Sprintf("output/%s.downloading", id)
		finalPath := fmt.Sprintf("output/%s/%s.zip", id[len(id)-3:], id)
		if _, err := os.Stat(targetPath); err == nil {
			// 如果targetPath已经存在，则调到下一个
			log("File %s already exists\n", targetPath)
			continue
		}

		if _, err := os.Stat(finalPath); os.IsNotExist(err) { // 如果文件不存在
			log("Downloading %s %s to %s \n", fastestIP, url, targetPath)
			if err := download(fastestIP, url, targetPath); err != nil {
				//第二次使用master 仓库名下载
				if err := download(fastestIP, url2, targetPath); err != nil {
					erro("Error downloading %s: %s  ID= %s \n", url2, err, id)
					continue
				} else {
					url = url2
				}
			}
			log("Downloaded %s.\n", url)
			// 将文件移动到目标位置
			if err := os.MkdirAll(filepath.Dir(finalPath), os.ModePerm); err != nil {
				erro("Error creating directory for %s: %s  ID= %s \n", finalPath, err, id)
				continue
			}
			if err := os.Rename(targetPath, finalPath); err != nil {
				erro("Error moving %s to %s: %s  ID= %s \n", targetPath, finalPath, err, id)
				continue
			}
			log("Moved %s to %s.\n", targetPath, finalPath)
		} else {
			log("Skipping download of %s, file already exists.\n", url)
		}
	}

	if err := scanner.Err(); err != nil {
		erro("Error reading file: %s\n", err)
	}
}

func download(ip string, url string, targetPath string) error {
	// 如果出现异常，则返回错误
	ua := "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36" // 如果不需要自定义 User-Agent 就设置为空字符串
	err := httpIPdownloader.DownloadFile(url, targetPath, ip, ua)
	return err
}
