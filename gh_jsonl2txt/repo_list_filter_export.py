import json
import zipfile
import os
import sys
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterator, *args, **kwargs):
        return iterator
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# 创建文件输出处理器
file_handler = logging.FileHandler('repo_list_filter_export.log')
file_handler.setLevel(logging.ERROR)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def process_zip_file(zip_file_path, output_file_path):
    # 打开zip文件
    with zipfile.ZipFile(zip_file_path, 'r') as myzip:
        # 遍历zip文件中的所有文件
        for file_name in myzip.namelist():
            # 如果文件是jsonl格式，则进行处理
            if file_name.endswith('.jsonl'):
                print(f"正在处理:{file_name}");
                with myzip.open(file_name) as f:
                    proc_file(f,output_file_path)

def process_dir(dir_path, output_file_path):
    # 遍历目录下的所有文件和子目录
    for root, dirs, files in os.walk(dir_path):
        for file_name in files:
            # 处理文件
            try:
                if file_name.endswith('.jsonl'):
                    print(f"正在处理:{file_name}");
                    with open(os.path.join(root, file_name)) as f:
                        proc_file(f, output_file_path)
            except:
                logger.error(f"压缩文件处理错误 \n{file_name}")
                continue


def proc_file(f,output_file_path):
        # 按行读取json数据
        for line in tqdm(f):
            if len(line.strip()) < 10:
                continue
            try:
                json_data = json.loads(line)
                if isinstance(json_data, str):
                    json_data = json.loads(json_data)

                stargazers_count = json_data.get('stargazers_count')
                watchers_count = json_data.get('watchers_count')
                forks_count = json_data.get('forks_count')
            except:
                logger.error(f"json解析错误，行：\n{line}")
                continue
            # 判断是否满足条件并将结果输出到文件
            if stargazers_count > 0 and watchers_count > 0 and forks_count > 0:
                id = json_data.get('id')
                clone_url = json_data.get('clone_url')
                with open(output_file_path, 'a') as output_file:
                    output_file.write(f'{id}, {clone_url}\n')

def gen_dir_by_id(data_dir, file_id):
    """
    将指定数据保存到指定编号的文件中
    """
    subdir = str(file_id % 1000)  # 三级子目录编号
    subdir = os.path.join(data_dir, subdir)  # 合并子目录路径

    if not os.path.exists(subdir):
        os.makedirs(subdir)  # 创建子目录
    
    return subdir

    #  = os.path.join(subdir, str(file_id) + '.txt')  # 合并文件名


def split_file(file_path, m):
    # 打开原始文件并按行读取内容
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # 根据 m 计算分割后文件的个数
    n = (len(lines) + m - 1) // m
    # 分割原始文件，并将每个子文件写入磁盘
    for i in range(n):
        start = i * m
        end = (i + 1) * m
        sub_file_path = os.path.join(gen_dir_by_id(f"{file_path}_subs",i),f"{os.path.basename(file_path)}_{i}.txt")
        with open(sub_file_path, 'w') as sub_file:
            sub_file.writelines(lines[start:end])

def delete_file(file_name):
    # 判断文件是否存在
    if not os.path.exists(file_name):
        return
    # 提示是否确认覆盖
    while True:
        choice = input(f"列表汇总文件 {file_name} 已存在，是否要覆盖？(y/n): ").strip().lower()
        if choice == 'n':
            return
        elif choice == 'y':
            try:
                # 删除文件
                os.remove(file_name)
            except Exception as e:
                print(f"覆盖文件 {file_name} 出现异常：{str(e)}")
            return
        else:
            print("请输入 y 或 n")

if __name__ == "__main__":
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("请提供要处理的jsonl zip 文件 or 目录、参数 m ")
    else:
        file_name = sys.argv[1]
        m = int(sys.argv[2])
        

        if (os.path.isfile(file_name)):
            delete_file(f"{file_name}.T")
            process_zip_file(file_name,f"{file_name}.T")
        else:
            out_file_path = os.path.join(file_name,"T")
            print(f"输出文件目录：{out_file_path}_subs/")
            print(f"汇总文件路径：{out_file_path}")
            delete_file(out_file_path)
            process_dir(file_name,out_file_path)
        split_file(out_file_path,m)
