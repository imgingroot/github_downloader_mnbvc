import os
import glob
import time
import shutil

import requests

from typing import List, Tuple
from pathlib import Path
import concurrent.futures

from requests.adapters import HTTPAdapter
from urllib.parse import urlparse
from urllib3.util.retry import Retry

from delete_zip_file import zipinfo_to_jsonl, get_zipfile_info, delete_from_zip_file
import traceback
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_ip_speed(hostname: str, ip: str):

    try:
        r = requests.head(f"https://{ip}", headers={"host": hostname}, verify=False, timeout=5)
        if r.status_code < 500:
            return {'ip': ip, 'speed': r.elapsed.microseconds, 'is_connected': True}
        else:
            return {'ip': ip, 'speed': r.elapsed.microseconds, 'is_connected': False}
    except:
        traceback.print_exc()
        return {'ip': ip, 'speed': float('inf'), 'is_connected': False}

def test_domain_ips(hostname: str, ips: List[str]) -> Tuple[str, List[dict], Exception]:
    speeds = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(test_ip_speed, hostname, ip): ip for ip in ips}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            speed = future.result()
            if speed['is_connected']:
                speeds.append(speed)

    if len(speeds) > 0:
        speeds.sort(key=lambda x: x['speed'])
        return speeds[0]['ip'], speeds, None
    else:
        return '', [], Exception('all IPs are not reachable')


def download_file(url: str, filename: str, ip: str, ua: str) -> Exception:
    host = urlparse(url).hostname
    headers = {'host': host}
    if ua:
        headers['User-Agent'] = ua

    if ip:
        url = url.replace(host, ip)

    try:
        with requests.get(url, headers=headers, stream=True, verify=False) as response:
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    shutil.copyfileobj(response.raw, file)
            else:
                return Exception(f'response error with status code = {response.status_code}')
    except Exception as e:
        return e

    return None


def download(ip: str, url: str, target_path: str) -> Exception:
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    err = download_file(url, target_path, ip, ua)
    return err


def start():
    ips = ["20.205.243.165", "199.59.148.9", "20.27.177.114", "192.30.255.121", "140.82.121.9", "140.82.121.10",
            "140.82.112.10", "140.82.113.9", "140.82.112.9", "140.82.114.10", "20.200.245.246", "140.82.113.10",
            "20.248.137.55", "20.207.73.88"]
    domain = "codeload.github.com"

    fastest_ip, spds, err = test_domain_ips(domain, ips)

    if err:
        print(err)
        return

    for s in spds:
        print(f"ip: {s['ip']}\t --> {s['speed']} ms \t[{s['is_connected']}]")

    filename = "repos_list.txt"
    print("Processing file:", filename)

    # 打开待处理文件
    with open(filename, 'r') as file:
        for line in file:
            # 解析行数据
            parts = line.strip().split(',')
            print(parts)
            rid = parts[0]
            addr = parts[1].strip()
            if len(rid) < 3:
                rid = rid.zfill(3)

            # 解析地址
            u = urlparse(addr)
            path_parts = u.path.split('/')
            if len(path_parts) < 3:
                print(f"Invalid URL: {addr}  ID= {rid}")
                continue
            author = path_parts[1]
            name = path_parts[2][:-4]

            # 拼接 URL 并下载文件https://github.com/imgingroot/httpIPdownloader/archive/refs/heads/main.zip
            url = f"https://codeload.github.com/{author}/{name}/zip/refs/heads/main"
            url2 = f"https://codeload.github.com/{author}/{name}/zip/refs/heads/master"
            target_path = f"output/{rid[-3:]}/{rid}.downloading"
            final_path = f"output/{rid[-3:]}/{rid}.zip"

            # 检查目录是否存在
            os.makedirs(os.path.dirname(final_path), exist_ok=True)

            if os.path.exists(target_path):
                continue

            if not os.path.exists(final_path):
                print(f"Downloading {fastest_ip} {url} to {target_path}")

                # 下载前，先touch一个 空文件
                Path(target_path).touch()
                err = download(fastest_ip, url, target_path)
                if err:
                    # 第二次使用master 仓库名下载
                    err = download(fastest_ip, url2, target_path)
                    if err:
                        print(f"Error downloading {url2}: {err}  ID= {rid}")
                        continue
                    else:
                        url = url2

                print(f"Downloaded {url}.")
                shutil.move(target_path, final_path)
                print(f"Moved {target_path} to {final_path}.")

                # jsonl文件名 
                json_file_path = final_path.replace(".zip", ".jsonl")
                # 判断 jsonl 文件是否存在，如果不存在，就调用 zipinfo 函数进行处理
                if not os.path.exists(json_file_path):
                    start_time = time.perf_counter()
                    zipinfo_to_jsonl(final_path, json_file_path, None, True)
                    exec_time = time.perf_counter() - start_time
                    print(f"zip文件 {final_path} 处理完成，耗时 {exec_time:.2f} 秒")


if __name__ == "__main__":
    start()
