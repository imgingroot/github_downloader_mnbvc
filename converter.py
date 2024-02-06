#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import io
import sys
import argparse
import json
import shutil
import logging
import time
import zipfile
import hashlib as hs
import traceback
from typing import List
from pathlib import PurePosixPath, Path, PosixPath
from charset_mnbvc import api
#######################################################
debug_mode = False
name_position = 3
# 其他变量
plateform = 'github'       # 仓库来自哪个平台
clean_src_file = False     # 是否删除源文件
#######################################################

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def is_file_locked(filename):
    for proc in psutil.process_iter(['pid', 'open_files']):
        try:
            for file in proc.info['open_files']:
                if os.path.abspath(filename) == file.path:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, TypeError):
            pass
    return False

class CodeFileInstance:
    def __init__(self, repo_path, file_path, target_encoding="utf-8", zf=None):
        if isinstance(file_path, PosixPath): 
            # 解压后的文件夹模式，此时的repo_path是解压后文件目录的Path对象，zf是None
            assert repo_path.exists(), f"{repo_path} is not exists."
            assert file_path.exists(), f"{file_path} is not exists."
            self._size = file_path.stat().st_size
            file_bytes = file_path.read_bytes()
            relate_file_path = file_path.relative_to(repo_path)
        else:  # 未解压的压缩包模式，此时的repo_path是zip文件的Path对象，zf是ZIPFile对象
            self._size = file_path.file_size
            relate_file_path = Path(file_path.filename)
            with zf.open(file_path.filename, 'r')as r: file_bytes = r.read()
        self._name = relate_file_path.stem
        self._ext = relate_file_path.suffix
        self._path = str(relate_file_path)
        self._encoding = api.from_data(file_bytes, mode=2)
        self._reponame = relate_file_path.parts[0]
        self.target_encoding = target_encoding
        text = None
        if self._encoding is not None:
            try:
                data = file_bytes.decode(encoding=self.target_encoding, errors='ignore')
                text = data.encode(encoding=target_encoding).decode(target_encoding, 'ignore')
            except Exception as err:
                print("================")
                traceback.print_exc()
                # sys.stderr.write(f"Error: {str(err)}\n")
            # text = charset_mnbvc.api.convert_encoding(file_bytes, self._encoding, self.target_encoding)
            # text可能会转码失败，输出的还是原编码文本
        self._text = text
        self._md5 = self.__get_content_md5(file_bytes)

    @property
    def encoding(self):
        return self._encoding

    @property
    def size(self):
        return self._size

    @property
    def text(self):
        return self._text

    @property
    def name(self):
        return self._name

    @property
    def ext(self):
        return self._ext

    @property
    def path(self):
        return self._path

    @property
    def md5(self):
        return self._md5

    def __get_content_md5(self, content: bytes):
        m = hs.md5()
        m.update(content)
        return m.hexdigest()

    def get_dict(self):
        return {
            "来源": "",
            "仓库名": self._reponame,
            "文件名": self.name+self.ext,
            "ext": self.ext,
            "path": self.path,
            "size": self.size,
            "原始编码": self.encoding,
            "md5": self.md5,
            "text": self.text,
            "时间": "20240000"
        }

class Zipfile2JsonL:
    def __init__(self, output_root, chunk_counter, target_encoding="utf-8", clean_src_file=False, plateform="github", author=""):
        if not os.path.exists(output_root): os.makedirs(output_root)
        self.output = Path(output_root)
        self.target_encoding = target_encoding
        self.max_jsonl_size = 500 * 1024 * 1024
        self.repo_list = list()
        # chunk_counter的值由run.py传入，默认为0
        self.chunk_counter = chunk_counter
        self.clean_src_file = clean_src_file
        self.plateform = plateform
        self.author = author
        
    def extract_without_unpack(self, zip_path):
        try:
            try:
                zf = zipfile.ZipFile(zip_path, "r")
            except zipfile.BadZipFile:  # 解压过程中遇到 Bad magic number for central directory 问题的解决办法
                with open(zip_path, "rb")as r: data=r.read()
                idx = data.find(b"PK\005\006")
                data = io.BytesIO(data[:idx+22])
                zf = zipfile.ZipFile(data, "r")
            for Zfile in zf.filelist:
                if Zfile.is_dir(): continue
                filepath = Zfile.filename
                code = CodeFileInstance(zip_path, Zfile, target_encoding="utf-8", zf=zf)
                self.save_code(code)
            zf.close()
        except Exception as e:
            traceback.print_exc()
            with open(self.output/"convert_error.log",'a')as a:
                a.write(str(zip_path)+'\n')

    def save_code(self, code):
        if code.encoding is None or not isinstance(code.text, str): return
        dic = code.get_dict()
        dic["来源"] = self.plateform
        dic["仓库名"] = self.author + "/" + dic['仓库名']
        with open(self.temp_name, "a", encoding="utf-8") as a1:
            a1.write(json.dumps(dic, ensure_ascii=False) + "\n")
        #if os.path.getsize(self.get_jsonl_file()) > self.max_jsonl_size:
        #    # 这里加上将jsonl压缩成zip包，如果压缩包位置已有文件占位，需要先删除占位文件（即防止写入报错）
        #    # jsonl压缩成zip包后，删除jsonl原文件
        #    self.create_zip(self.get_jsonl_file())
        #    self.chunk_counter += 1

    def get_zipfile(self, file_path):
        # 因为仓库压缩包的文件名不一定是仓库的文件名，所以专门指定一个路径
        repo_root = file_path.parent / ('zipout-' + file_path.stem)
        try:
            # raise OSError # 用作测试直接不解压提取
            if repo_root.exists(): shutil.rmtree(repo_root)
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(repo_root)
            except zipfile.BadZipFile:  # 解压过程中遇到 Bad magic number for central directory 问题的解决办法
                if repo_root.exists(): shutil.rmtree(repo_root)
                with open(file_path, 'rb')as r: data=r.read()
                idx = data.find(b"PK\005\006")
                data = io.BytesIO(data[:idx+22])
                with zipfile.ZipFile(data, 'r')as zf:
                    zf.extractall(repo_root)
            file_list = repo_root.rglob("**/*")
            for file in file_list:
                if not file.is_file(): continue
                code = CodeFileInstance(repo_root, file, self.target_encoding)
                self.save_code(code)
        except:
            # 这里尝试用下面注释的代码直接从zip包里读取文件
            self.extract_without_unpack(file_path)
        self.temp2jsonl()
        if repo_root.exists(): shutil.rmtree(repo_root) # 删除解压生成的文件夹

    def temp2jsonl(self):
        if not os.path.exists(self.temp_name): return
        # while is_file_locked(self.get_jsonl_file()):
        #     time.sleep(1)
        if os.path.exists(self.get_jsonl_file()):
            size1 = os.path.getsize(self.get_jsonl_file())
        else: size1 = 0
        size2 = os.path.getsize(self.temp_name)
        if size1 + size2 <= self.max_jsonl_size:
            # 如果写入后不超过限制，就直接写入
            with open(self.temp_name, "r", encoding="utf-8")as r, open(self.get_jsonl_file(), "a", encoding="utf-8")as a:
                a.write(r.read())
            os.unlink(self.temp_name)
        else:
            # 如果超过限制，就将原jsonl打包成zip，将临时jsonl改名成新的最终jsonl
            self.create_zip(self.get_jsonl_file())
            os.unlink(self.get_jsonl_file())
            self.chunk_counter += 1
            shutil.move(self.temp_name, self.get_jsonl_file())

    def create_zip(self, jsonl_path):
        zip_path = str(jsonl_path).rsplit(".", 1)[0] + ".zip"
        if os.path.exists(zip_path): os.unlink(zip_path)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_BZIP2)as zf:
            zf.write(jsonl_path)

    def return_counter(self):
        # 返回chunk_counter，否则run.py不知道counter是否有增加
        return self.chunk_counter

    def get_jsonl_file(self):
        return self.output / f"githubcode.{self.chunk_counter}.jsonl"

    def __call__(self, zip_path, final=False):
        zip_path = Path(zip_path)
        self.temp_name = self.output / ("tempFile_" + zip_path.stem)  # 本仓库的临时jsonl文件
        if os.path.exists(self.temp_name): os.unlink(self.temp_name)
        assert zip_path.exists(), FileNotFoundError(str(zip_path))
        self.get_zipfile(zip_path)
        if self.clean_src_file is True:
            zip_path.unlink()
        if final is True and os.path.exists(self.get_jsonl_file()): # 最后一个仓库解析完打成压缩包
            self.create_zip(self.get_jsonl_file())
