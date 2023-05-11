import os
import argparse
import logging
import cchardet as chardet
import zipfile
import json
from datetime import datetime

from ruamel.std.zipfile import delete_from_zip_file


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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
                with zf.open(info, 'r') as file:
                    dsize = temp_zip_size
                    if temp_zip_size > 32*1024:
                        dsize = 32*1024

                    content = file.read(dsize)
                    encoding = chardet.detect(content)['encoding']
                    text = None

                    if encoding is not None and with_text:
                        #详细检测内码
                        file.seek(0)
                        content = file.read()
                        encoding = chardet.detect(content)['encoding']
                        if encoding is not None:
                            text = content.decode(encoding)

                    yield {
                        "file_name": os.path.basename(info.filename),
                        "ext": os.path.splitext(info.filename)[-1].strip('.'),
                        "path": info.filename,
                        "size": temp_zip_size,
                        "encoding": encoding,
                        "created_at": datetime(*temp_zip_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        "modified_at": datetime(*temp_zip_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "text": text
                    }

def create_jsonl(file_path, file_infos):
    """生成 jsonl 文件"""
    with open(file_path, 'w') as f:
        for file_info in file_infos:
            json.dump(file_info, f)
            
            f.write('\n')
    # logger.info(f"生成的 JSONL 文件为: {file_path}")


def zipinfo_to_jsonl(input_path:str,output_path:str,file_json_path:str,delete_non_text=False):
    # 获取所有文件信息并写入 JSONL 文件
    try:
        file_infos = list(get_zipfile_info(input_path))
        if len(file_infos) < 1:
            logger.error(f"压缩包为空: {str(input_path)}")
            return 0
        if output_path is not None:
            create_jsonl(output_path, file_infos)
        if delete_non_text:
            #删除非文本文件
            # 打开zip文件
            del_list = []
            for file_info in file_infos:
                if file_info["encoding"] == None:
                    del_list.append(file_info["path"])
                elif file_info["size"] > 10*1024*1024:
                    del_list.append(file_info["path"])

            if len(del_list) > 0 :
                logger.info(f"删除非文本文件 {len(del_list)}个")
            delete_from_zip_file(input_path,file_names=del_list)

        if file_json_path is not None:
            file_infos = list(get_zipfile_info(input_path,True))
            create_jsonl(file_json_path, file_infos)

        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="输入压缩包的路径")
    parser.add_argument("-o", "--output", required=False, default=None, help="输出 文件信息JSONL 文件路径")
    parser.add_argument("-d", "--delete-non-text", required=False, action="store_true", help="是否删除非文本文件，默认为否")
    parser.add_argument("-t", "--text-jsonl-output", required=False, default=None, help="导出文本文件的路径")
    args = parser.parse_args()
    if args.output is None and args.text_jsonl_output is None:
        parser.error("-o 和 -t 参数不能同时为空")


    zipinfo_to_jsonl(args.input, args.output,args.text_jsonl_output, args.delete_non_text)
