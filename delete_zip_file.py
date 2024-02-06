#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 本代码有如下用途：
#   1.单独运行，可以将目录下所有zip内代码数据去除二进制文件
#   2.process_zips方法会被run.py调用，每下载完一个zip，用这个方法删除一下zip包内的二进制文件
#   3.原本用于提取zip内文件明细，进行统计的代码已废弃
import argparse
import logging
import os
import time
import zipfile
from datetime import datetime
from traceback import print_exc

from charset_mnbvc import api
from ruamel.std.zipfile import delete_from_zip_file

logging.basicConfig(level=logging.ERROR, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def get_zipfile_info(zip_path, with_text=False):
    """获取压缩包中所有文件信息"""
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if not info.is_dir():
                temp_zip_info = zf.getinfo(info.filename)
                temp_zip_size = temp_zip_info.file_size
                temp_zip_ctime = temp_zip_info.date_time
                temp_zip_mtime = temp_zip_info.date_time
                yield {
                    "file_name": os.path.basename(info.filename),
                    "ext": os.path.splitext(info.filename)[-1].strip('.'),
                    "path": info.filename,
                    "size": temp_zip_size,
                    "info": info,
                    "zip_path": zip_path,
                    "created_at": datetime(*temp_zip_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    "modified_at": datetime(*temp_zip_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                }


def process_zip(input_path: str):
    '''删除zip包中二进制文件'''
    try:
        # 获取压缩包内的每个文件信息
        file_infos = list(get_zipfile_info(input_path))
        # 如果压缩包没有文件，直接返回
        if len(file_infos) < 1:
            logger.error(f"压缩包为空: {str(input_path)}")
            return 0
        # 需删除的文件列表
        del_list = []
        # 需要删除的后缀
        delete_suffix = ["DS_Store",]
        # 需要跳过的后缀
        whitelist_suffix = []
        # 所有suffix
        all_suffix = {}
        # 遍历统计本库中suffix的平均大小
        for file_info in file_infos:
            if file_info["ext"] in all_suffix:
                all_suffix[file_info["ext"]]["num"] += 1
                all_suffix[file_info["ext"]]["size"] += file_info["size"]
                all_suffix[file_info["ext"]]["avg"] = all_suffix[file_info["ext"]]["size"] / \
                                                      all_suffix[file_info["ext"]]["num"]
            else:
                all_suffix[file_info["ext"]] = {}
                all_suffix[file_info["ext"]]["num"] = 1
                all_suffix[file_info["ext"]]["size"] = file_info["size"]
                all_suffix[file_info["ext"]]["avg"] = file_info["size"]
                all_suffix[file_info["ext"]]["notBnum"] = 0
        # 遍历suffix，将需要删除的suffix放入list中
        for key, value in all_suffix.items():
            if value["avg"] > 200 * 1024:
                delete_suffix.append(key)
        big_32k_file = 0
        check_times = 10
        for file_info in file_infos:
            # 如果是白名单后缀则跳过
            if file_info["ext"] in whitelist_suffix:
                continue
            # 删除本仓库平均后缀大小大于200k的后缀
            elif file_info["ext"] in delete_suffix:
                del_list.append(file_info["path"])
            # 删除大于1mb的文件
            elif file_info["size"] > 1 * 1024 * 1024:
                del_list.append(file_info["path"])
            # 删除长度大于15的文件
            # elif len(file_info["ext"]) > 15:
            #     del_list.append(file_info["path"])
            # 如果文件大于32k，读取全文件看是否二进制，如是，本仓库所有该后缀文件直接删除
            else:
                if file_info["size"] <= 32 * 1024:
                    continue
                # 下面3行代码用于处理后缀特别多的超大压缩包
                big_32k_file += 1
                if big_32k_file > 1000:
                    check_times = 1
                try:
                    with zipfile.ZipFile(file_info["zip_path"]) as zf:
                        with zf.open(file_info["info"], 'r') as file:
                            chunk = file.read()
                            # 判断为二进制或编码判断不出编码
                            if b'\0' in chunk or api.from_data(chunk, mode=1) is None:
                                del_list.append(file_info["path"])
                                if len(file_info["ext"]) > 0:
                                    delete_suffix.append(file_info["ext"])
                            else:
                                if all_suffix[file_info["ext"]]["notBnum"] >= check_times:
                                    whitelist_suffix.append(file_info["ext"])
                                else:
                                    all_suffix[file_info["ext"]]["notBnum"] += 1
                except Exception as e:
                    print(file_info["zip_path"])
                    print_exc()
        if len(del_list) > 0:
            logger.info(f"删除非文本文件 {len(del_list)}个")
            delete_from_zip_file(input_path, file_names=del_list)
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
            # 记录开始时间
            start_time = time.perf_counter()
            process_zip(file_path)
            # 计算并输出执行时间
            exec_time = time.perf_counter() - start_time
            print(f'zip文件 {file_path} 处理完成，耗时 {exec_time:.2f} 秒')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="输入压缩包的路径")
    args = parser.parse_args()
    process_zips(args.input)
