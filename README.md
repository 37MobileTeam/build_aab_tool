# apk转化aab格式

### 在线工具-aab转换工具

[https://aab.sfhaa.com](https://aab.sfhaa.com)

### 使用流程

* 运行环境 python3.6 +

* 安装需要的环境

    ```shell
    pip install -r requirements.txt
    ```

* 执行命令生成aab

    ```shell
    python bundletool.py -i test.apk -o test.aab
    ```

  参数说明:
    ```
      -h 
    
    ​		show this help message and exit
      -i 
    
    ​		输入apk的路径
      -o 
    
    ​		输出apk的路径
      --keystore 
    
    ​		签名文件路径
      --store_password 
    
    ​		签名文件路径
      --key_alias 
    
    ​		签名文件路径
      --key_password 
    
    ​		签名文件路径
      --apktool 
    
    ​		apktool.jar路径
      --aapt2 
    
    ​		aapt2路径
      --android 
    
    ​		android.jar 路径
      --bundletool 
    
    ​		bundletool.jar 路径
      --pad_reg 
    
    ​		正则表达式，从assets里面去剪切文件构建pad模块 例如: ^\d.*\.map$ 剪切以数字开头 .map 结尾的文件到pad目录
  ```


* 详细说明

  配套博客为:[https://juejin.cn/post/6982111395621896229](https://juejin.cn/post/6982111395621896229)

### License

build_aab_tool is released under the [Apache 2.0 license](LICENSE).

```
Copyright 2021 37手游安卓团队

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
