# coding=utf-8
import os
import datetime
import shutil
import zipfile
import yaml
import xml.etree.ElementTree as ET
import platform
import argparse
import time
import sys

WINDOWS = "Windows"
Linux = "Linux"
MACOS = "Darwin"

sep = os.sep
APKTOOL_PATH = f"tools{sep}apktool-2.5.2-fix.jar"
AAPT2_PATH = f"tools{sep}30.0.3{sep}aapt2"
ANDROID_JAR_PATH = f"tools{sep}android_30.jar"
BUNDLETOOL_TOOL_PATH = f"tools{sep}bundletool-all-1.6.1.jar"


KEYSTORE = f"tools{sep}luojian37.jks"
STORE_PASSWORD = "luojian37"
KEY_ALIAS = "luojian37"
KEY_PASSWORD = "luojian37"


def get_system():
    return platform.system()


def execute_cmd(cmd):
    print("#"*10, cmd)
    status = os.system(cmd)
    return status, ""


def zip_file(src_dir, zip_name=""):
    if not zip_name:
        zip_name = src_dir + '.zip'
    z = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(src_dir):
        fpath = dirpath.replace(src_dir, '')
        fpath = fpath and fpath + os.sep or ''
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath+filename)
    z.close()
    return 0, "success"


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        print('This is not zip')
        return -1, "This is not zip"
    return 0, "success"


def delete(path):
    if not os.path.exists(path):
        return 0, "success"
    if os.path.isfile(path):
        os.remove(path)
    else:
        platform_system = get_system()
        cmd = ""
        if platform_system == WINDOWS:
            cmd = f"rd /s /q {path}"
        elif platform_system == Linux:
            cmd = f"rm -rf {path}"
        elif platform_system == MACOS:
            cmd = f"rm -rf {path}"

        if not cmd:
            shutil.rmtree(path)
        else:
            return execute_cmd(cmd)

    return 0, "success"


def copy(source_path, target_path):
    if not os.path.exists(source_path):
        return 0, "文件不存在，但是直接给成功。有的项目没有lib文件夹"
    if os.path.isfile(source_path):
        target_dirname = os.path.dirname(target_path)
        if not os.path.exists(target_dirname):
            # 如果目标路径不存在原文件夹的话就创建
            os.makedirs(target_dirname)
    if os.path.exists(target_path):
        # 如果目标路径存在原文件夹的话就先删除
        status, msg = delete(target_path)
        if status != 0:
            return status, msg
    if os.path.isdir(source_path):
        shutil.copytree(source_path, target_path)
    else:
        shutil.copyfile(source_path, target_path)
    return 0, "success"


class Bundletool:

    def check_system(self):
        status = 0
        print(f"[当前系统]:{get_system()}")
        print(f"[当前系统JAVA版本]↓↓↓↓↓:")
        status, msg = execute_cmd("java -version")
        print(f"[输入apk]:{self.input_apk_path}")
        if not os.path.exists(self.input_apk_path):
            return -1, f"输入的apk不存在:{self.input_apk_path}"
        print(f"[输出aab]:{self.out_aab_path}")
        print(
            f"[签名]:{self.keystore},storepass:{self.storepass},alias:{self.alias},keypass:{self.keypass}")
        if not os.path.exists(self.keystore):
            return -2, f"输入的keystore不存在:{self.keystore}"
        status, msg = execute_cmd(
            f"keytool -list -v -keystore {self.keystore} -storepass {self.storepass} -alias {self.alias} ")
        status += status
        print(f"↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
        if get_system() in [MACOS, Linux]:
            status, msg = execute_cmd(
                f"keytool -exportcert -alias {self.alias} -keystore {self.keystore} -storepass {self.storepass} | openssl sha1 -binary | openssl base64")
            if status != 0:
                return -999, "签名错误"
        else:
            print("window不去校验，避免没有openssl的库")
        print(f"↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")
        print(f"[apktool]:{self.apktool}")
        print(f"[apktool版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"java -jar {self.apktool} --version")
        status += status
        print(f"[aapt2]:{self.aapt2}")
        print(f"[aapt2版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"{self.aapt2} version")
        status += status
        print(f"[android]:{self.android}")
        if not os.path.exists(self.android):
            return -3, f"输入的android.jar不存在:f{self.android}"
        print(f"[bundletool]:{self.bundletool}")
        print(f"[bundletool版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"java -jar {self.bundletool} version")
        status += status
        return status, "success"

    def analysis_apk(self):
        content = ""
        with open(self.decode_apk_apktool_path, "r") as f:
            content = f.read()
        content = content.replace("!!brut.androlib.meta.MetaInfo", "")
        data = yaml.load(content, Loader=yaml.FullLoader)
        sdk_info = data["sdkInfo"]
        self.min_sdk_version = sdk_info["minSdkVersion"]
        self.target_sdk_version = sdk_info["targetSdkVersion"]

        version_info = data["versionInfo"]
        self.version_code = version_info["versionCode"]
        self.version_name = version_info["versionName"]
        return 0, "success"

    def decode_apk(self):
        cmd = f"java -jar {self.apktool} d {self.input_apk_path} -s -o {self.decode_apk_dir}"
        return execute_cmd(cmd)

    def delete_sign(self):
        meta_inf_list = os.listdir(self.decode_apk_meta_inf_path)
        for i in meta_inf_list:
            if not i.endswith(".RSA") or not i.endswith(".SF") or not i.endswith(".MF"):
                continue
            delete(os.path.abspath(i))
        return 0, "success"

    def compile_resources(self):
        compile_source_res_dir = os.path.join(self.decode_apk_dir, "res")
        cmd = f"{self.aapt2} compile --legacy\
            --dir {compile_source_res_dir} \
            -o {self.compiled_resources}"
        return execute_cmd(cmd)

    def link_resources(self):
        compiled_resources_path = f"{self.compiled_resources}"
        cmd = f"{self.aapt2} link --proto-format \
            -o {self.link_base_apk_path} \
            -I {self.android} \
            --min-sdk-version {self.min_sdk_version} \
            --target-sdk-version {self.target_sdk_version}\
            --version-code {self.version_code}\
            --version-name {self.version_name}\
            --manifest {self.decode_apk_android_manifest_path} \
            -R {compiled_resources_path} \
            --auto-add-overlay"
        return execute_cmd(cmd)

    def copy_dex(self):
        dex_array = list(filter(lambda x: x.endswith(
            "dex"), os.listdir(self.decode_apk_dir)))
        dex_path_array = list(
            map(lambda x: os.path.join(self.decode_apk_dir, x), dex_array))
        for dex in dex_path_array:
            basename = os.path.basename(dex)
            status, msg = copy(dex, os.path.join(
                self.link_base_dex_dir, basename))
            if status != 0:
                return status, msg
        return 0, "success"

    def build_bundle(self):
        cmd = f"java -jar {self.bundletool} build-bundle \
            --modules={self.link_base_zip_path} \
            --output={self.temp_aab_path}"
        return execute_cmd(cmd)

    def sign(self):
        cmd = f"jarsigner -digestalg SHA1 -sigalg SHA1withRSA \
            -keystore {self.keystore} \
            -storepass {self.storepass} \
            -keypass {self.keypass} \
            {self.temp_aab_path} \
            {self.alias}"
        return execute_cmd(cmd)

    def task(self, task_name, fun, *args, **kwargs):
        print(f"---{task_name}")
        start_time = time.time()
        status, msg = fun(*args, **kwargs)
        end_time = time.time()
        print(
            f"###耗时:{end_time - start_time} {task_name} status:{status} msg:{msg}")
        if status != 0:
            raise Exception(f"task {task_name} 执行异常status:{status} msg:{msg}")

    def run(self, input_apk_path, out_aab_path,
            keystore=KEYSTORE, storepass=STORE_PASSWORD, alias=KEY_ALIAS, keypass=KEY_PASSWORD,
            apktool=APKTOOL_PATH,
            aapt2=AAPT2_PATH,
            android=ANDROID_JAR_PATH,
            bundletool=BUNDLETOOL_TOOL_PATH):

        tag = False

        self.input_apk_path = os.path.abspath(input_apk_path)
        self.out_aab_path = os.path.abspath(out_aab_path)
        self.keystore = os.path.abspath(keystore)
        self.storepass = storepass
        self.alias = alias
        self.keypass = keypass
        self.apktool = os.path.abspath(apktool)
        self.aapt2 = os.path.abspath(aapt2)
        self.android = os.path.abspath(android)
        self.bundletool = os.path.abspath(bundletool)

        # 生成临时的工作目录
        temp_dir = f"temp_{'{0:%Y%m%d%H%M%S}'.format(datetime.datetime.now())}"
        temp_dir = "temp"

        self.min_sdk_version = 19
        self.target_sdk_version = 30
        self.version_code = 1
        self.version_name = "1.0.0"

        # if os.path.exists(temp_dir):
        #     delete(temp_dir)
        os.mkdir(temp_dir)

        self.decode_apk_dir = os.path.join(temp_dir, "decode_apk_dir")
        self.decode_apk_apktool_path = os.path.join(
            self.decode_apk_dir, "apktool.yml")
        self.decode_apk_android_manifest_path = os.path.join(
            self.decode_apk_dir, "AndroidManifest.xml")
        self.decode_apk_assets_path = os.path.join(
            self.decode_apk_dir, "assets")
        self.decode_apk_lib_path = os.path.join(
            self.decode_apk_dir, "lib")
        self.decode_apk_unknown_path = os.path.join(
            self.decode_apk_dir, "unknown")
        self.decode_apk_kotlin_path = os.path.join(
            self.decode_apk_dir, "kotlin")
        self.decode_apk_meta_inf_path = os.path.join(
            self.decode_apk_dir, "original", "META-INF")

        self.compiled_resources = os.path.join(
            temp_dir, f"compiled_resources.zip")
        self.link_base_apk_path = os.path.join(temp_dir, "base.apk")
        self.link_base_path = os.path.join(temp_dir, "base")
        self.link_base_zip_path = os.path.join(temp_dir, "base.zip")
        # aapt2生成的AndroidManifest的位置，需要移动到manifest目录下面去
        self.link_base_temp_android_manifest_path = os.path.join(
            self.link_base_path, "AndroidManifest.xml")

        self.link_base_android_manifest_path = os.path.join(
            self.link_base_path, "manifest", "AndroidManifest.xml")
        self.link_base_assets_path = os.path.join(
            self.link_base_path, "assets")
        self.link_base_lib_path = os.path.join(
            self.link_base_path, "lib")
        self.link_base_root_path = os.path.join(
            self.link_base_path, "root")
        self.link_base_root_kotlin_path = os.path.join(
            self.link_base_root_path, "kotlin")
        self.link_base_root_meta_inf_path = os.path.join(
            self.link_base_root_path, "META-INF")
        self.link_base_dex_dir = os.path.join(
            self.link_base_path, "dex")

        self.temp_aab_path = os.path.join(temp_dir, "base.aab")

        try:
            self.task("环境&参数校验", self.check_system)
            self.task("解压input_apk", self.decode_apk)
            self.task("解析apk信息", self.analysis_apk)
            try:
                # 资源文件的开头是 '$' 的，存在编译失败的问题。但是好像并不影响程序的使用，正常开发也不会存在$开头的文件,
                # 文件怎么来的？
                self.task("编译资源", self.compile_resources)
            except:
                pass
            self.task("关联资源", self.link_resources)
            self.task("解压resources_apk", unzip_file,
                      self.link_base_apk_path, self.link_base_path)
            self.task("拷贝AndroidManifest", copy, self.link_base_temp_android_manifest_path,
                      self.link_base_android_manifest_path)
            self.task("清除AndroidManifest", delete,
                      self.link_base_temp_android_manifest_path)
            self.task("拷贝assets", copy, self.decode_apk_assets_path,
                      self.link_base_assets_path)
            self.task("拷贝lib", copy, self.decode_apk_lib_path,
                      self.link_base_lib_path)
            self.task("拷贝unknown", copy, self.decode_apk_unknown_path,
                      self.link_base_root_path)
            self.task("拷贝kotlin", copy, self.decode_apk_kotlin_path,
                      self.link_base_root_kotlin_path)
            self.task("处理原有的apk签名信息", self.delete_sign)
            # 拷贝META-INF的时候需要先删除 apk的签名信息
            self.task("拷贝META-INF", copy, self.decode_apk_meta_inf_path,
                      self.link_base_root_meta_inf_path)
            self.task("拷贝dex", self.copy_dex)
            self.task("压缩base.zip", zip_file, self.link_base_path,
                      self.link_base_zip_path)
            self.task("构建aab", self.build_bundle)
            self.task("签名", self.sign)
            self.task("拷贝输出拷贝", copy, self.temp_aab_path, self.out_aab_path)
        except Exception as e:
            print(e)
            tag = True
            pass

        status, msg = delete(temp_dir)
        print(f"执行完成，删除临时文件。输出路径:{self.out_aab_path}")
        if tag:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="37手游apk转aab")
    parser.add_argument("-i", "--input", help="输入apk的路径", required=True)
    parser.add_argument("-o", "--output", help="输出apk的路径", required=True)
    parser.add_argument("--keystore", help="签名文件路径", default=KEYSTORE)
    parser.add_argument("--store_password", help="签名文件路径",
                        default=STORE_PASSWORD)
    parser.add_argument("--key_alias", help="签名文件路径", default=KEY_ALIAS)
    parser.add_argument("--key_password", help="签名文件路径", default=KEY_PASSWORD)
    parser.add_argument("--apktool", help="apktool.jar路径",
                        default=APKTOOL_PATH)
    parser.add_argument("--aapt2", help="aapt2路径", default=AAPT2_PATH)
    parser.add_argument("--android", help="android.jar 路径",
                        default=ANDROID_JAR_PATH)
    parser.add_argument(
        "--bundletool", help="bundletool.jar 路径", default=BUNDLETOOL_TOOL_PATH)
    args = parser.parse_args()

    input_apk_path = os.path.abspath(args.input)
    output_aab_path = os.path.abspath(args.output)
    keystore = args.keystore
    store_password = args.store_password
    key_alias = args.key_alias
    key_password = args.key_password
    apktool = args.apktool
    aapt2 = args.aapt2
    android = args.android
    bundletool = args.bundletool

    Bundletool().run(input_apk_path=input_apk_path,
                     out_aab_path=output_aab_path,
                     keystore=keystore,
                     storepass=store_password,
                     alias=key_alias,
                     keypass=key_password,
                     apktool=apktool,
                     aapt2=aapt2,
                     android=android,
                     bundletool=bundletool)

    pass
