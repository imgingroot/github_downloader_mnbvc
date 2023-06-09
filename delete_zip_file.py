#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import json
import logging
import os
import time
import zipfile
from datetime import datetime

from ruamel.std.zipfile import delete_from_zip_file

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

ext_list = ["zip", "rar", "7z", "nib", "sim", "train", "stats", "wav", "pg", "png", "gif", "jpg", "svn-base", "class",
            "out", "jar", "glif", "dat", "o", "pdf", "gz", "md5", "bmp", "ico", "tga", "acc"]


def get_zipfile_info(zip_path, with_text=False):
    """获取压缩包中所有文件信息"""
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if not info.is_dir():
                temp_zip_info = zf.getinfo(info.filename)
                temp_zip_size = temp_zip_info.file_size
                temp_zip_ctime = temp_zip_info.date_time
                temp_zip_mtime = temp_zip_info.date_time
                # with zf.open(info, 'r') as file:
                #     dsize = temp_zip_size
                #     if temp_zip_size > 32 * 1024:
                #         dsize = 32 * 1024
                #
                #     content = file.read(dsize)
                #     encoding = chardet.detect(content)['encoding']
                #     text = None
                #
                #     if encoding is not None and with_text:
                #         # 详细检测内码
                #         file.seek(0)
                #         content = file.read()
                #         encoding = chardet.detect(content)['encoding']
                #         if encoding is not None:
                #             text = content.decode(encoding)

                yield {
                    "file_name": os.path.basename(info.filename),
                    "ext": os.path.splitext(info.filename)[-1].strip('.'),
                    "path": info.filename,
                    "size": temp_zip_size,
                    "encoding": "",
                    "info": info,
                    "zip_path": zip_path,
                    "created_at": datetime(*temp_zip_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    "modified_at": datetime(*temp_zip_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "text": ""
                }


def create_jsonl(file_path, file_infos):
    """生成 jsonl 文件"""
    with open(file_path, 'w') as f:
        for file_info in file_infos:
            json.dump(file_info, f)

            f.write('\n')
    # logger.info(f"生成的 JSONL 文件为: {file_path}")


def zipinfo_to_jsonl(input_path: str, output_path: str, file_json_path: str, delete_non_text=False):
    # 获取所有文件信息并写入 JSONL 文件
    # 获取所有文件信息并写入 JSONL 文件
    try:
        file_infos = list(get_zipfile_info(input_path))
        if len(file_infos) < 1:
            logger.error(f"压缩包为空: {str(input_path)}")
            return 0
        # if output_path is not None:
        #     create_jsonl(output_path, file_infos)
        if delete_non_text:
            # 删除非文本文件
            # 打开zip文件
            del_list = []
            #需要删除的后缀
            delete_suffix=[]
            #所有suffix
            all_suffix={}
            #遍历统计本库中suffix的平均大小
            for file_info in file_infos:
                if file_info["ext"] in all_suffix:
                    all_suffix[file_info["ext"]]["num"] += 1
                    all_suffix[file_info["ext"]]["size"] += file_info["size"]
                    all_suffix[file_info["ext"]]["avg"] = all_suffix[file_info["ext"]]["size"] / all_suffix[file_info["ext"]]["num"]
                else:
                    all_suffix[file_info["ext"]] = {}
                    all_suffix[file_info["ext"]]["num"] = 1
                    all_suffix[file_info["ext"]]["size"] = file_info["size"]
                    all_suffix[file_info["ext"]]["avg"] = file_info["size"]
            #遍历suffix，将需要删除的suffix放入list中
            for key, value in all_suffix.items():
                if value["avg"] > 200 * 1024:
                    delete_suffix.append(key)
            for file_info in file_infos:
                #删除本仓库平均后缀大小大于200k的后缀
                if file_info["ext"] in delete_suffix:
                    del_list.append(file_info["path"])
                #删除大于1mb的文件
                elif file_info["size"] > 1 * 1024 * 1024:
                    del_list.append(file_info["path"])
                #删除长度大于15的文件
                elif len(file_info["ext"]) > 15:
                    del_list.append(file_info["path"])
                #如果文件大于32k，读取前32k字节看是否包含b'\0',当发现有后，本仓库所有该后缀文件直接删除
                else:
                    if file_info["size"] <= 32 * 1024:
                        continue
                    try:
                        with zipfile.ZipFile(file_info["zip_path"]) as zf:
                            with zf.open(file_info["info"], 'r') as file:
                                dsize = 32 * 1024
                                chunk = file.read(dsize)
                                if b'\0' in chunk:
                                    del_list.append(file_info["path"])
                                    if len(file_info["ext"]) > 0:
                                        delete_suffix.append(file_info["ext"])
                    except Exception as e:
                        traceback.print_exc()
            if len(del_list) > 0:
                print(del_list)
                logger.info(f"删除非文本文件 {len(del_list)}个")
                delete_from_zip_file(input_path, file_names=del_list)

        # if file_json_path is not None:
        #     file_infos = list(get_zipfile_info(input_path, True))
        #     create_jsonl(file_json_path, file_infos)
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")


def process_zips(root_dir):
    """递归遍历目录中的 zip 文件并调用 zipinfo 函数处理"""
    # 获取当前目录下的所有文件和文件夹
    file_list = os.listdir(root_dir)
    for file_name in file_list:
        # 获取文件的完整路径
        file_path = os.path.join(root_dir, file_name)
        # 判断是否为目录，如果是则进行递归遍历
        if os.path.isdir(file_path):
            process_zips(file_path)
        # 如果是 zip 文件则进行处理
        elif file_name.endswith('.zip'):
            # 构造结果文件名
            json_file_name = file_name.replace('.zip', '.jsonl')
            # 构造完整路径
            json_file_path = os.path.join(root_dir, json_file_name)
            # 判断 json 文件是否存在，如果不存在就调用 zipinfo 函数进行处理
            if not os.path.exists(json_file_path):
                # 记录开始时间
                start_time = time.perf_counter()
                zipinfo_to_jsonl(file_path, json_file_path, None, True)
                # 计算并输出执行时间
                exec_time = time.perf_counter() - start_time
                print(f'zip文件 {file_path} 处理完成，耗时 {exec_time:.2f} 秒')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="输入压缩包的路径")
    parser.add_argument("-o", "--output", required=False, default=None, help="输出 文件信息JSONL 文件路径")
    parser.add_argument("-d", "--delete-non-text", required=False, action="store_true", help="是否删除非文本文件，默认为否")
    parser.add_argument("-t", "--text-jsonl-output", required=False, default=None, help="导出文本文件的路径")
    args = parser.parse_args()
    # if args.output is None and args.text_jsonl_output is None:
    #     parser.error("-o 和 -t 参数不能同时为空")
    process_zips(args.input)
    # zipinfo_to_jsonl(args.input, args.output, args.text_jsonl_output, args.delete_non_text)