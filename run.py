import os
import time
import shutil
import zipfile
import urllib3
import requests
import concurrent.futures

from pathlib import Path
from urllib.parse import urlparse

from delete_zip_file import process_zip

from converter import Zipfile2JsonL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_ip_speed(hostname: str, ip: str):
    try:
        r = requests.head(f"https://{ip}", headers={"host": hostname}, verify=False, timeout=5)
        if r.status_code < 500:
            return {'ip': ip, 'speed': r.elapsed.microseconds, 'is_connected': True}
        else:
            return {'ip': ip, 'speed': r.elapsed.microseconds, 'is_connected': False}
    except:
        return {'ip': ip, 'speed': float('inf'), 'is_connected': False}

def find_fastest_ip():
    ips = ["20.205.243.165", "199.59.148.9", "20.27.177.114", "192.30.255.121", "140.82.121.9", "140.82.121.10",
            "140.82.112.10", "140.82.113.9", "140.82.112.9", "140.82.114.10", "20.200.245.246", "140.82.113.10",
            "20.248.137.55", "20.207.73.88"]
    domain = "codeload.github.com"
    speeds = list()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(test_ip_speed, domain, ip): ip for ip in ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            speed = future.result()
            if speed['is_connected']:
                speeds.append(speed)

    if len(speeds) > 0:
        speeds.sort(key=lambda x: x['speed'])
        return speeds[0]['ip'], speeds, None
    else:
        return '', [], Exception('all IPs are not reachable')

def download(url, filename, fastest_ip):
    '''具体下载操作'''
    print('----', url, '----')
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    host = urlparse(url).hostname
    headers = {"host": host, "User-Agent": ua}
    if fastest_ip:
        url = url.replace(host, fastest_ip, 1)

    try:
        resp = requests.get(url, headers=headers, stream=True, verify=False)
        if resp.status_code == 200:
            with open(filename, "wb")as writer:
                for chunk in resp.iter_content(chunk_size=1024*1024):
                    if chunk: writer.write(chunk)
            print("download finished")
        else:
            return Exception(f'response error with status code = {resp.status_code}')
    except Exception as e:
        return e

def down(fastest_ip, url, final_path):
    '''下载逻辑'''
    target_path = final_path[:-4] + ".downloading"

    print(f"Downloading {fastest_ip} {url} to {target_path}")

    # 如果此前已有downloading文件，说明之前下载未完成，删除历史文件重新下载
    if os.path.exists(target_path): os.unlink(target_path)
    # 优先使用main下载，若不成功再尝试使用master
    err = download(url, target_path, fastest_ip)
    print('err1', err)
    if err:
        # 第二次使用master 仓库名下载
        url = url[:-4] + "master"
        err = download(url, target_path, fastest_ip)
        print('err2', err)
        if err: return err

    print(f"Downloaded {url}.")
    shutil.move(target_path, final_path)
    print(f"Moved {target_path} to {final_path}.")

def parse_one_line(line, fastest_ip):
    rid, addr = line.strip().split(",", 1)
    addr = addr.strip()
    if len(rid) < 3: rid = rid.zfill(3)

    path_parts = urlparse(addr).path.split('/')
    if len(path_parts) < 3:
        print(f"Invalid URL: {addr}   ID={rid}")
        return
    
    author = path_parts[1]
    name = path_parts[2][:-4]

    # 拼接 URL 并下载文件https://github.com/imgingroot/httpIPdownloader/archive/refs/heads/main.zip
    url = f"https://codeload.github.com/{author}/{name}/zip/refs/heads/main"
    final_path = f"output/zips/{rid}.zip"

    # 检查目录是否存在
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    if not os.path.exists(final_path):
        # 下载仓库压缩包
        err = down(fastest_ip, url, final_path)
        if err is not None:
            print(f"Error downloading {url}: {err}  ID= {rid}")
            with open("output/error.log", "a", encoding='utf-8')as a:
                a.write(f"{rid}\t{url}\t{err}\n")
    
    if os.path.exists(final_path):
        print("parsing zip file")
        # 删除zip文件中的二进制文件
        process_zip(final_path)
        # 提取代码语料到jsonl
        handler = Zipfile2JsonL("output/jsonl", target_encoding="utf-8", clean_src_file=False, plateform="github", author=author)
        handler(final_path)
        print("zip file parsed.")

def main():

    filename = "repos_list.txt"

    fastest_ip, speeds, err = find_fastest_ip()

    print("Fastest IP:", fastest_ip)
    if err is not None:
        print(err)
        return
    for s in speeds:
        print(f"ip: {s['ip']}\t --> {s['speed']} ms \t[{s['is_connected']}]")
   
    done_set = set()
    if os.path.exists("./.done"):
        with open("./.done",'r',encoding='utf-8')as r:
            done_set.update(r.read().split("\n"))

    with open(filename, "r", encoding="utf-8")as reader:
        for line in reader:
            rid, addr = line.strip().split(",", 1)
            if rid in done_set:
                print(rid, 'exists. PASS')
                continue
            parse_one_line(line, fastest_ip)
            with open("./.done", "a", encoding='utf-8')as a:
                a.write(rid+"\n")
            done_set.add(rid)

if __name__ == '__main__':
    main()
