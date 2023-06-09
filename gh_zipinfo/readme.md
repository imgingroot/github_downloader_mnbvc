zipinfo是处理单个仓库的zip文件，生成文件信息json，并可以删除其中的非文本文件。
zipdir 是调用zipinfo 批量处理一个目录下所有的zip，可以在下载的同时运行。

zipdir的目的是考虑打包成exe，方便小白用户使用，没有参数，程序会自动获取当前工作目录作为初始目录进行操作。 
使用方法： 把两个文件放到下载好zip仓库的目录，直接运行 zipdir.py 

----

以下是 `zipinfo` 程序的说明文档：

## 程序简介

`zipinfo_to_jsonl` 程序可以将指定 ZIP 文件中的所有文件信息提取为 JSON 格式并写入文件，或者删除指定格式或大小的非文本文件，以及按照不同内码导出文本文件的信息列表。

## 程序实现

程序基于 Python 语言，使用了以下第三方库：

- `os`：提供了一些与操作系统交互的函数。
- `argparse`：提供了命令行参数解析的功能。
- `logging`：提供了日志记录的框架。
- `cchardet`：提供了检测文件内码的功能。
- `zipfile`：提供了 ZIP 文件的读取和写入功能。
- `json`：提供了 JSON 格式的编码和解码功能。
- `datetime`：提供了日期和时间处理的功能。
- `ruamel`：提供了创建和修改 ZIP 文档的功能。

具体实现过程如下：

1. 使用 `argparse` 库解析用户输入参数。
2. 使用 `zipfile` 库打开指定的 ZIP 文件，并遍历文件信息列表。
3. 对于列表中的每一个文件，读取其文件名、扩展名、路径、大小、内码、创建时间、修改时间等信息。
4. 如果用户要求，对于后缀名为非文本格式或文件大小超过 10MB 的文件进行删除。
5. 如果用户要求，检测所有文件的内码，将其转成 Unicode 编码。
6. 将所有文件信息保存为 JSON 格式，并写入到指定的文件中。

## 程序使用

程序命令行使用参数如下：

```
-i, --input 输入压缩包的路径
-o, --output 输出文件信息 JSONL 文件路径
-t, --text-jsonl-output 导出文本文件的路径
-d, --delete-non-text 是否删除非文本文件，默认为否
```

-i/--input：必选参数，输入压缩包的路径。
-o/--output：可选参数，输出文件信息的 JSONL 文件路径。
-t/--text-jsonl-output：可选参数，导出文本文件的路径，输出文件信息的 JSONL 文件路径。
-d/--delete-non-text：可选参数，是否删除非文本文件，默认为否。
