#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
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
from pathlib import PurePosixPath, Path
from charset_mnbvc import api

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Zipfile2JsonL:
    def __init__(self, output_root, target_encoding="utf-8", clean_src_file=False, plateform="github", author=""):
        if not os.path.exists(output_root): os.makedirs(output_root)
        self.output = Path(output_root)
        self.target_encoding = target_encoding
        self.max_jsonl_size = 500 * 1024 * 1024
        self.repo_list = list()
        self.clean_src_file = clean_src_file
        self.plateform = plateform
        self.author = author
        self.numLog_file = os.path.join(output_root, '.numLog_file')

    def get_md5(self, content):
        m = hs.md5()
        m.update(content)
        return m.hexdigest()

    def get_zipfile(self, zip_path):
        # 不解压，直接读取文件内容
        # 记录写入的文件，防止在某个仓库处理过程中停止后导致该仓库前面写过的文件重复写入
        temp_done_set = set()
        if os.path.exists(".temp_done"):
            with open(".temp_done","r",encoding="utf-8")as r:
                temp_done_set.update([i.strip() for i in r.readlines()])
        with zipfile.ZipFile(zip_path, "r") as zf:
            for Zfile in zf.filelist:
                try:
                    if Zfile.is_dir(): continue
                    filepath = Zfile.filename
                    if filepath in temp_done_set: continue
                    filesize = Zfile.file_size
                    fileobj = Path(filepath)
                    filename = fileobj.stem
                    fileext = fileobj.suffix
                    with zf.open(filepath, 'r')as f:
                        bdata = f.read()
                    fileencoding = api.from_data(bdata, mode=2)
                    fileplate = self.plateform
                    filerepos = self.author + "/" + fileobj.parts[0]
                    filemd5 = self.get_md5(bdata)
                    if fileencoding is not None and fileencoding != "UNKNOWN":
                        try:
                            data = bdata.decode(encoding=fileencoding)
                            filetext = data.encode(encoding=self.target_encoding).decode(encoding=self.target_encoding)
                        except UnicodeDecodeError:
                            continue
                    else:
                        continue

                    dic = dict()
                    dic['plateform'] = fileplate
                    dic['repo_name'] = filerepos
                    dic['path'] = filepath
                    dic['name'] = filename+fileext
                    dic['ext'] = fileext
                    dic['size'] = filesize
                    dic['source_encoding'] = fileencoding
                    dic['md5'] = filemd5
                    dic['text'] = filetext

                    self.save_data(dic) # 写入jsonl

                    with open(".temp_done", "a", encoding='utf-8')as a2:
                        a2.write(str(filepath) + "\n")
                except Exception as e:
                    with open("ERR",'a')as a:
                        a.write(traceback.format_exc()+"\n\n\n\n")
                    traceback.print_exc()

        open(".temp_done","w",encoding="utf-8").close()

    def create_zip(self, file_path):
        zip_path = file_path.rsplit(".", 1)[0] + ".zip"
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_BZIP2)as zf:
            zf.write(file_path)

    def save_data(self, dic):
        num = self.get_jsonl_num()
        out_file_name = str(self.output / f"githubcode.{num}.jsonl")
        with open(out_file_name, "a", encoding="utf-8")as a1:
            a1.write(json.dumps(dic, ensure_ascii=False) + "\n")
        if os.path.getsize(out_file_name) >= self.max_jsonl_size:
            # 如果jsonl超过最大限制，压缩，再开启一个新的jsonl
            self.create_zip(out_file_name)
            os.unlink(out_file_name)
            with open(self.numLog_file, "w", encoding="utf-8")as w:
                w.write(str(num+1))

    def get_jsonl_num(self):
        if os.path.exists(self.numLog_file):
            with open(self.numLog_file, "r", encoding="utf-8")as r:
                num = int(r.read())
        else: num = 0
        return num
        # return self.output / f"githubcode.{num}.jsonl"

    def __call__(self, zip_path):
        zip_path = Path(zip_path)
        assert zip_path.exists(), FileNotFoundError(str(root_dir))
        self.get_zipfile(zip_path)
        if self.clean_src_file is True:
            zip_path.unlink()

