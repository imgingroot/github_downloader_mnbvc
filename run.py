import os
import time
import shutil
import zipfile
import urllib3
import requests
import concurrent.futures

from pathlib import Path
from urllib.parse import urlparse

from delete_zip_file import process_zips

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
        # with requests.get(url, headers=headers, stream=True, verify=False) as response:
        #     if response.status_code == 200:
        #         with open(filename, 'wb') as file:
        #             shutil.copyfileobj(response.raw, file)
        #     else:
        #         return Exception(f'response error with status code = {response.status_code}')
    except Exception as e:
        return e

def down(fastest_ip, url, final_path):
    '''下载逻辑'''
    target_path = final_path[:-4] + ".downloading"

    print(f"Downloading {fastest_ip} {url} to {target_path}")

    # 下载前，先touch一个 空文件
    if os.path.exists(target_path): os.unlink(target_path)
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

def gen_jsonl(final_path):
    # jsonl文件名 
    json_file_path = final_path.replace(".zip", ".jsonl")
    # 判断 jsonl 文件是否存在，如果不存在，就调用 zipinfo 函数进行处理
    if not os.path.exists(json_file_path):
        start_time = time.perf_counter()
        # zipinfo_to_jsonl(final_path, json_file_path, None, True)
        final_folder = final_path.rsplit("/", 1)[0]
        process_zips(final_folder, final_folder)
        exec_time = time.perf_counter() - start_time
        print(f"zip文件 {final_path} 处理完成，耗时 {exec_time:.2f} 秒")

def pack_zip_file():
    name_before_zip = 'output-' + time.strftime("%Y%m%d-%H%M%S")
    shutil.move("output", name_before_zip)
    ziper = zipfile.ZipFile(name_before_zip+".zip", "w", zipfile.ZIP_DEFLATED)
    for path, dirname, filenames in os.walk(name_before_zip):
        fpath = path.replace(name_before_zip, '')
        for fn in filenames:
            ziper.write(os.path.join(path, fn), os.path.join(fpath, fn))
    ziper.close()
    shutil.rmtree(name_before_zip)
    
def parse_one_line(line, fastest_ip):
    global output_size
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
    final_path = f"output/{rid[-3:]}/{rid}.zip"

    # 检查目录是否存在
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    if not os.path.exists(final_path):
        err = down(fastest_ip, url, final_path)
        if err is not None:
            print(f"Error downloading {url}: {err}  ID= {rid}")
            with open("output/error.log", "a", encoding='utf-8')as a:
                a.write(f"{rid}\t{url}\t{err}\n")
    
    if os.path.exists(final_path):
        print("parsing zip file")
        gen_jsonl(final_path)
        print("zip file parsed.")
        output_size += os.path.getsize(final_path)
        output_size += os.path.getsize(final_path[:-4]+'.jsonl')
        output_size += os.path.getsize(final_path[:-4]+'.meta.jsonl')
        if output_size >= 1024*1024*10:  # 大于10g，打包一下
            pack_zip_file()
        output_size = 0

def main():

    filename = "repos_list.txt"
    global output_size
    output_size = 0
    for a,_,b in os.walk('output'):
        for j in b:
            output_size += os.path.getsize(os.path.join(a, j))

    fastest_ip, speeds, err = find_fastest_ip()
    print("Fastest IP:", fastest_ip)
    if err is not None:
        print(err)
        return
    for s in speeds:
        print(f"ip: {s['ip']}\t --> {s['speed']} ms \t[{s['is_connected']}]")

    with open(filename, "r", encoding="utf-8")as reader:
        for line in reader:
            parse_one_line(line, fastest_ip)
    if os.listdir("output"): pack_zip_file()

if __name__ == '__main__':
    main()
