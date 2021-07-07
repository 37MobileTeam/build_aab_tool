# apk转化aab格式

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
  ```


 * 详细说明

    配套博客为:[https://juejin.cn/post/6982111395621896229](https://juejin.cn/post/6982111395621896229)