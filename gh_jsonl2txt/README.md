# repo_list_filter_export

把github repo api的jsonl过滤导出txt的程序


使用方法：
```
python3 repo_list_filter_export.py jsonl.zip 1000
```

输入可以是压缩包也可以是目录，1000 是把txt同时拆解到1000个文件

输出的文件在jsonl.zip的同目录 T 为总文件，T_subs目录下为拆解后的文件。


