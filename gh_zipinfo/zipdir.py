import os
import sys
import time
from zipinfo import zipinfo_to_jsonl


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
            code_json_file_name = file_name.replace('.zip', '.code.jsonl')
            # 构造完整路径
            json_file_path = os.path.join(root_dir, json_file_name)
            code_json_file_path = os.path.join(root_dir, code_json_file_name)
            # 判断 json 文件是否存在，如果不存在就调用 zipinfo 函数进行处理
            if not os.path.exists(json_file_path):
                # 输出调试信息，包含文件大小
                file_size = os.path.getsize(file_path)
                if file_size < 1024:
                    file_size_str = f'{file_size:.0f} B'
                elif file_size < 1024 * 1024:
                    file_size_str = f'{file_size / 1024:.2f} KB'
                elif file_size < 1024 * 1024 * 1024:
                    file_size_str = f'{file_size / 1024 / 1024:.2f} MB'
                else:
                    file_size_str = f'{file_size / 1024 / 1024 / 1024:.2f} GB'
                print(f'开始处理zip文件: {file_path}，大小为：{file_size_str}')
                # 记录开始时间
                start_time = time.perf_counter()
                zipinfo_to_jsonl(file_path, json_file_path, None, True)
                # 计算并输出执行时间
                exec_time = time.perf_counter() - start_time
                print(f'zip文件 {file_path} 处理完成，耗时 {exec_time:.2f} 秒')

# 解析命令行参数
if len(sys.argv) > 1:
    root_dir = sys.argv[1]
else:
    root_dir = os.getcwd()

# 输出调试信息
print(f'开始执行程序，初始目录: {root_dir}')

# 循环执行任务
while True:
    # 记录开始时间
    start_time = time.perf_counter()
    # 执行任务
    process_zips(root_dir)
    # 计算并输出执行时间
    exec_time = time.perf_counter() - start_time
    print(f'本次遍历完成，耗时 {exec_time:.2f} 秒')
    # 等待 15 分钟
    time.sleep(15 * 60)
