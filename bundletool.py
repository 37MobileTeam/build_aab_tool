# coding=utf-8
import datetime
import json
import re
import yaml
import argparse
import time
import sys

import xml.etree.ElementTree as ET

from files_pb2 import Assets
from google.protobuf import json_format

if hasattr(sys, "_flask"):
    from .utils import *
else:
    try:
        from utils import *
    except:
        from .utils import *


def print_log(message):
    if global_print_fun:
        global_print_fun(message)
    else:
        print(message)
    pass


def get_base_dir() -> str:
    if hasattr(sys, "_flask"):
        return os.path.dirname(os.path.realpath(__file__))
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return ""


APKTOOL_PATH = os.path.join(get_base_dir(), "tools", "apktool-2.5.2-fix.jar")
AAPT2_PATH = os.path.join(get_base_dir(), "tools", "aapt2", get_system(), "aapt2")
ANDROID_JAR_PATH = os.path.join(get_base_dir(), "tools", "android_30.jar")
BUNDLETOOL_TOOL_PATH = os.path.join(get_base_dir(), "tools", "bundletool-all-1.6.1.jar")

KEYSTORE = os.path.join(get_base_dir(), "tools", "luojian37.jks")
STORE_PASSWORD = "luojian37"
KEY_ALIAS = "luojian37"
KEY_PASSWORD = "luojian37"

BUNDLE_MODULE_TEMPLATE_PATH = os.path.join(get_base_dir(), "tools", "pad_template")


def task(task_name, fun, *args, **kwargs):
    print_log(f"---{task_name}")
    start_time = time.time()
    status, msg = fun(*args, **kwargs)
    end_time = time.time()
    print_log(f"###耗时:{end_time - start_time} {task_name} status:{status} msg:{msg}")
    if status != 0:
        raise Exception(f"task {task_name} 执行异常status:{status} msg:{msg}")


def compile_resources(compile_source_res_dir: str, compiled_resources: str, aapt2: str):
    """
    编译 res目录
    :param compile_source_res_dir: res文件夹的路径
    :param compiled_resources: 输出的路径
    :param aapt2: aapt2
    :return:
    """
    cmd = f"{aapt2} compile --legacy\
        --dir {compile_source_res_dir} \
        -o {compiled_resources} "
    return execute_cmd(cmd)


def link_asset_resources(link_out_apk_path: str,
                         input_manifest: str,
                         android: str,
                         aapt2: str):
    """
    生成一个apk
    :param link_out_apk_path: 生成临时apk的路径
    :param input_manifest: 需要的manifest的路径
    :param android: android的jar
    :param aapt2: aapt2的路径
    :return:
    """
    cmd = f"{aapt2} link --proto-format \
        -o {link_out_apk_path} \
        -I {android} \
        --manifest {input_manifest} \
        --auto-add-overlay"
    return execute_cmd(cmd)


def link_resources(link_out_apk_path: str,
                   input_manifest: str,
                   android: str,
                   min_sdk_version: str,
                   target_sdk_version: str,
                   version_code: str,
                   version_name: str,
                   aapt2: str,
                   compiled_resources_path: str = None,
                   public_id_path: str = None):
    """
    生成一个apk
    :param link_out_apk_path: 生成临时apk的路径
    :param input_manifest: 需要的manifest的路径
    :param android: android的jar
    :param min_sdk_version: 最低的版本号
    :param target_sdk_version: 目标版本号
    :param version_code: apk的版本号
    :param version_name: apk的版本名
    :param aapt2: aapt2的路径
    :param compiled_resources_path: 编译后res.zip的路径
    :return:
    """
    cmd = f"{aapt2} link --proto-format \
        -o {link_out_apk_path} \
        -I {android} \
        --min-sdk-version {min_sdk_version} \
        --target-sdk-version {target_sdk_version}\
        --version-code {version_code}\
        --version-name {version_name}\
        --manifest {input_manifest} \
        --auto-add-overlay"

    if compiled_resources_path and os.path.exists(compiled_resources_path):
        cmd += f" -R {compiled_resources_path}"
    if public_id_path and os.path.exists(public_id_path):
        cmd += f" --stable-ids {public_id_path}"
    return execute_cmd(cmd)


def delete_sign(meta_inf_path):
    """
    删除apk里面的签名信息
    :param meta_inf_path: 存放签名信息的文件夹
    :return:
    """
    meta_inf_list = os.listdir(meta_inf_path)
    for i in meta_inf_list:
        if not i.endswith(".RSA") or not i.endswith(".SF") or not i.endswith(".MF"):
            continue
        delete(os.path.abspath(i))
    return 0, "success"


def copy_dex(base_dir_path, target_dex_path):
    """
    拷贝dex
    :param base_dir_path: 资源的目录
    :param target_dex_path: 目标目录
    """
    dex_array = list(filter(lambda x: x.endswith("dex"), os.listdir(base_dir_path)))
    dex_path_array = list(
        map(lambda x: os.path.join(base_dir_path, x), dex_array))
    for dex in dex_path_array:
        basename = os.path.basename(dex)
        status, msg = copy(dex, os.path.join(target_dex_path, basename))
        if status != 0:
            return status, msg
    return 0, "success"


def build_bundle(bundletool: str, modules: str, out_aab_path: str, bundle_config_json_path: str = None):
    """
    构建aab
    :param bundletool: 构架工具
    :param modules: 需要构建的module， 多个module用 , 隔开
    :param out_aab_path: 输出的aab的路径
    :param bundle_config_json_path: 构建config的配置文件
    """
    cmd = f"java -jar {bundletool} build-bundle \
        --modules={modules} \
        --output={out_aab_path} "
    if bundle_config_json_path and os.path.exists(bundle_config_json_path):
        cmd += f" --config={bundle_config_json_path}"
    return execute_cmd(cmd)


def decode_apk(apk_path: str, decode_apk_dir: str, apktool: str = None):
    cmd = f"java -jar {apktool} d {apk_path} -s -o {decode_apk_dir}"
    return execute_cmd(cmd)


def pad_mv_assets(base_dir, pad_dir, pad_reg):
    """
    从base apk里面拷贝资源到pad里面去
    :param base_dir: apk的解压路径
    :param pad_dir: pad的路径
    :param pad_reg: pad挑选资源所需要的正则表达式
    :return: 结果
    """
    base_dir = os.path.join(base_dir, "assets")
    pad_dir = os.path.join(pad_dir, "assets")
    file_name_list = get_file_name_list(base_dir)
    pattern = re.compile(pad_reg)
    # 正则匹配到需要移动的文件
    mv_file_name = []
    for file_name in file_name_list:
        temp_file_name = file_name[1:] if file_name[0] == "/" or file_name[0] == "\\" else file_name
        if pattern.match(temp_file_name):
            # 添加到需要移动的list集合里面去
            mv_file_name.append(temp_file_name)
    for temp in mv_file_name:
        mv(os.path.join(base_dir, temp),
           os.path.join(pad_dir, temp))
    return 0, "success"


def create_pad_module_dir(temp_dir, module_name, package):
    """
    创建一个module目录
    :param temp_dir: 存放module目录的位置
    :param module_name: module模块名
    :param package: apk的包名
    :return: 返回信息
    """
    status, message = copy(BUNDLE_MODULE_TEMPLATE_PATH, temp_dir)
    if status != 0:
        return status, message
    template_android_manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
    text = read_file_text(template_android_manifest_path) \
        .replace("$padName", module_name) \
        .replace("$applicationId", package)
    write_file_text(template_android_manifest_path, text)
    return 0, "success"


def sign(temp_aab_path, keystore, storepass, keypass, alias):
    cmd = f"jarsigner -digestalg SHA1 -sigalg SHA1withRSA \
        -keystore {keystore} \
        -storepass {storepass} \
        -keypass {keypass} \
        {temp_aab_path} \
        {alias}"
    return execute_cmd(cmd)


def create_bundle_config_json(bundle_config_json_path: str, do_not_compress: list):
    glob_not_compress = ['**.3[gG]2', '**.3[gG][pP]', '**.3[gG][pP][pP]', '**.3[gG][pP][pP]2', '**.[aA][aA][cC]',
                         '**.[aA][mM][rR]', '**.[aA][wW][bB]', '**.[gG][iI][fF]', '**.[iI][mM][yY]', '**.[jJ][eE][tT]',
                         '**.[jJ][pP][eE][gG]', '**.[jJ][pP][gG]', '**.[mM]4[aA]', '**.[mM]4[vV]', '**.[mM][iI][dD]',
                         '**.[mM][iI][dD][iI]', '**.[mM][kK][vV]', '**.[mM][pP]2', '**.[mM][pP]3', '**.[mM][pP]4',
                         '**.[mM][pP][eE][gG]', '**.[mM][pP][gG]', '**.[oO][gG][gG]', '**.[oO][pP][uU][sS]',
                         '**.[pP][nN][gG]', '**.[rR][tT][tT][tT][lL]', '**.[sS][mM][fF]', '**.[tT][fF][lL][iI][tT][eE]',
                         '**.[wW][aA][vV]', '**.[wW][eE][bB][mM]', '**.[wW][eE][bB][pP]', '**.[wW][mM][aA]',
                         '**.[wW][mM][vV]', '**.[xX][mM][fF]']
    do_not_compress = list(filter(lambda x: not x.startswith("META-INF"), do_not_compress))
    do_not_compress += glob_not_compress
    # {"compression": {"uncompressedGlob": ["foo"]},"bundletool":{}}
    config = {"bundletool": {"version": "1.2.3"}, "compression": {"uncompressedGlob": do_not_compress}, }
    data = json.dumps(config)
    write_file_text(bundle_config_json_path, data)
    return 0, "success"


class Bundletool:

    def __init__(self, keystore=KEYSTORE,
                 storepass=STORE_PASSWORD,
                 alias=KEY_ALIAS,
                 keypass=KEY_PASSWORD,
                 apktool=APKTOOL_PATH,
                 aapt2=AAPT2_PATH,
                 android=ANDROID_JAR_PATH,
                 bundletool=BUNDLETOOL_TOOL_PATH,
                 print_fun=None):
        global global_print_fun
        global_print_fun = print_fun
        # 初始化环境
        self.pad_reg = ""
        self.keystore = os.path.abspath(keystore)
        self.storepass = storepass
        self.alias = alias
        self.keypass = keypass
        self.apktool = os.path.abspath(apktool)
        self.aapt2 = os.path.abspath(aapt2)
        self.android = os.path.abspath(android)
        self.bundletool = os.path.abspath(bundletool)

        # apk的版本信息
        self.min_sdk_version = 19
        self.target_sdk_version = 30
        self.version_code = 1
        self.version_name = "1.0.0"
        self.apk_package_name = ""

        self.do_not_compress = []

        # 构建的module集合
        self.bundle_modules = {}
        self.bundle_asset_pack_modules = {}

    def check_system(self, apk_path, out_aab_path):
        print_log(f"[当前系统]:{get_system()}")
        print_log(f"[当前系统JAVA版本]↓↓↓↓↓:")
        _, msg = execute_cmd("java -version")
        print_log(f"[输入apk]:{apk_path}")
        if not os.path.exists(apk_path):
            return -1, f"输入的apk不存在:{apk_path}"
        print_log(f"[输出aab]:{out_aab_path}")
        print_log(f"[签名]:{self.keystore},storepass:{self.storepass},alias:{self.alias},keypass:{self.keypass}")
        if not os.path.exists(self.keystore):
            return -2, f"输入的keystore不存在:{self.keystore}"
        status, msg = execute_cmd(
            f"keytool -list -v -keystore {self.keystore} -storepass {self.storepass} -alias {self.alias} ")
        status += status
        print_log(f"↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓")
        if get_system() in [MACOS, Linux]:
            status, msg = execute_cmd(
                f"keytool -exportcert -alias {self.alias} -keystore {self.keystore} -storepass {self.storepass} | openssl sha1 -binary | openssl base64")
            if status != 0:
                return -999, "签名错误"
        else:
            print_log("window不去校验，避免没有openssl的库")
        print_log(f"↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑")
        print_log(f"[apktool]:{self.apktool}")
        print_log(f"[apktool版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"java -jar {self.apktool} --version")
        status += status
        # 如果是linux 或者 mac 需要给aapt可执行权限
        if get_system() in [MACOS, Linux]:
            try:
                execute_cmd(f"chmod +x {self.aapt2}")
            except Exception as e:
                print_log("授权失败:", e)
                pass
            pass
        print_log(f"[aapt2]:{self.aapt2}")
        print_log(f"[aapt2版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"{self.aapt2} version")
        status += status
        print_log(f"[android]:{self.android}")
        if not os.path.exists(self.android):
            return -3, f"输入的android.jar不存在:f{self.android}"
        print_log(f"[bundletool]:{self.bundletool}")
        print_log(f"[bundletool版本号]:↓↓↓↓↓")
        status, msg = execute_cmd(f"java -jar {self.bundletool} version")
        status += status
        return status, "success"

    def build_public_id(self, public_path, decode_apk_dir):
        apk_public_path = os.path.join(decode_apk_dir, "res", "values", "public.xml")
        tree = ET.parse(apk_public_path)
        root = tree.getroot()
        s = []
        for i in root:
            x_type = i.attrib["type"]
            x_name = i.attrib["name"]
            x_id = i.attrib["id"]
            s.append(f"{self.apk_package_name}:{x_type}/{x_name} = {x_id}\n")
        write_file_text(public_path, "".join(s))
        return 0, "success"

    def analysis_apk(self, decode_apk_dir):
        content = read_file_text(os.path.join(decode_apk_dir, "apktool.yml"))
        content = content.replace("!!brut.androlib.meta.MetaInfo", "")
        data = yaml.load(content, Loader=yaml.FullLoader)
        sdk_info = data["sdkInfo"]
        self.min_sdk_version = sdk_info["minSdkVersion"]
        self.target_sdk_version = sdk_info["targetSdkVersion"]

        version_info = data["versionInfo"]
        self.version_code = version_info["versionCode"]
        self.version_name = version_info["versionName"]

        self.do_not_compress = data["doNotCompress"]

        tree = ET.parse(os.path.join(decode_apk_dir, "AndroidManifest.xml"))
        root = tree.getroot()
        package = root.attrib["package"]
        self.apk_package_name = package
        return 0, "success"

    def is_pad(self):
        return len(self.pad_reg) > 0

    def build_asset_pack(self, temp_dir: str, module_name: str, input_resources_dir: str, out_module_zip_path: str):
        # 构建的临时目录
        module_temp_dir = os.path.join(temp_dir, f"{module_name}_temp")
        # 创建一下
        os.makedirs(module_temp_dir)
        # 生成的临时apk
        link_base_apk_path = os.path.join(module_temp_dir, f"{module_name}.apk")
        # 解压临时apk后的文件夹路径
        unzip_link_apk_path = os.path.join(module_temp_dir, module_name)
        # 解压后临时文件夹，AndroidManifest的路径
        temp_android_manifest_path = os.path.join(unzip_link_apk_path, "AndroidManifest.xml")
        # 构建的AndroidManifest.xml文件, 构建后删除
        input_manifest = os.path.join(input_resources_dir, "AndroidManifest.xml")
        # 最终的manifest的路径
        target_manifest_path = os.path.join(input_resources_dir, "manifest", "AndroidManifest.xml")
        # 构建
        task(f"[{module_name}]-asset-关联资源", link_asset_resources, link_base_apk_path, input_manifest, self.android,
             self.aapt2)
        # 解压
        task(f"[{module_name}]-asset-解压resources_apk", unzip_file, link_base_apk_path, unzip_link_apk_path)
        # 拷贝
        task(f"[{module_name}]-asset-移动AndroidManifest", mv, temp_android_manifest_path, target_manifest_path)
        # 删除
        task(f"[{module_name}]-asset-删除AndroidManifest", delete, input_manifest)

        # 构建asset.pb文件
        asset_path = input_resources_dir
        asset_dir_list = []
        for root, dirs, files in os.walk(asset_path):
            for i in dirs:
                is_statistics = False
                for t in os.listdir(os.path.join(root, i)):
                    if os.path.isfile(os.path.join(root, i, t)):
                        is_statistics = True
                        break
                # print(i, dirs, files)
                if not is_statistics:
                    continue
                path = os.path.join(root, i).replace("\\", os.sep).replace("/", os.sep)
                if not asset_path.endswith(os.sep):
                    asset_path = asset_path + os.sep
                path = path.replace(asset_path, "")
                asset_dir_list.append(path)

        asset_dir_list = list(filter(lambda x: x.startswith("assets"), asset_dir_list))
        asset_dir_list = list(map(lambda x: x.replace("\\", "/"), asset_dir_list))
        asset_dir_list = list(map(lambda x: {"path": x, "targeting": {}}, asset_dir_list))

        my_asset_obj = {
            "directory": asset_dir_list
        }
        my_asset_json_str = json.dumps(my_asset_obj)
        asset_config = json_format.Parse(my_asset_json_str, Assets())
        data = asset_config.SerializeToString()

        open(os.path.join(input_resources_dir, "assets.pb"), "wb").write(data)
        return 0, "success"

    def build_module_zip(self, temp_dir: str, module_name: str, input_resources_dir: str, out_module_zip_path: str,
                         public_id_path: str = None):
        """
        :param temp_dir: 构建的临时根目录
        :param module_name: module的名字
        :param input_resources_dir: 资源路径
        :param out_module_zip_path: 输出的zip文件的路径
        :return:
        """
        # 用于存放临时的module的目录
        module_dir_temp = os.path.join(temp_dir, module_name + "_temp")
        os.makedirs(module_dir_temp)
        # res资源的位置
        input_res_dir = os.path.join(input_resources_dir, "res")
        # 原始的AndroidManifest.xml的位置
        input_manifest = os.path.join(input_resources_dir, "AndroidManifest.xml")
        # 输入的assets目录
        input_assets = os.path.join(input_resources_dir, "assets")
        # 输入的lib的目录
        input_lib = os.path.join(input_resources_dir, "lib")
        # 输入的其他文件的路径
        input_unknown = os.path.join(input_resources_dir, "unknown")
        # 输入的kotlin
        input_kotlin = os.path.join(input_resources_dir, "kotlin")
        # 输入的签名信息
        input_meta_inf_path = os.path.join(input_resources_dir, "original", "META-INF")
        # 编译res之后的 zip文件的路径
        compiled_resources = os.path.join(module_dir_temp, "compiled_resources.zip")
        # 编译产生中间产物 apk的路径
        link_base_apk_path = os.path.join(module_dir_temp, "base.apk")
        # 解压编译后目录，用来做构建zip的根目录
        unzip_link_apk_path = os.path.join(module_dir_temp, module_name)

        # 中间生成的AndroidManifest的路径
        temp_android_manifest_path = os.path.join(unzip_link_apk_path, "AndroidManifest.xml")
        # 最终的AndroidManifest的路径
        target_android_manifest_path = os.path.join(unzip_link_apk_path, "manifest", "AndroidManifest.xml")
        # 最终的assets的目录
        target_assets_path = os.path.join(unzip_link_apk_path, "assets")
        # 最终的lib的路径
        target_lib_path = os.path.join(unzip_link_apk_path, "lib")
        # 最终的unknown的路径
        target_unknown_path = os.path.join(unzip_link_apk_path, "root")
        # 最终的kotlin的路径
        target_kotlin_path = os.path.join(target_unknown_path, "kotlin")
        # 最终的META-INF的路径
        target_mata_inf_path = os.path.join(target_unknown_path, "META-INF")
        # 最终存放dex的路径
        target_dex_path = os.path.join(unzip_link_apk_path, "dex")

        # 1. 编译res 生成 compiled_resources.zip
        # 如果存在res目录才执行这一步操作，pad不一定有这个目录
        if os.path.exists(input_res_dir):
            try:
                # 资源文件的开头是 '$' 的，存在编译失败的问题。但是好像并不影响程序的使用，正常开发也不会存在$开头的文件,
                # 文件怎么来的？
                task(f"[{module_name}]-编译资源", compile_resources, input_res_dir, compiled_resources, self.aapt2)
            except Exception as e:
                print_log(f"[{module_name}]-编译资源错误 {str(e)}")
                pass
        # 2. 通过 compiled_resources.zip 和 AndroidManifest.xml 生成中间产物 base.apk
        task(f"[{module_name}]-关联资源", link_resources, link_base_apk_path, input_manifest, self.android,
             self.min_sdk_version,
             self.target_sdk_version, self.version_code, self.version_name, self.aapt2, compiled_resources,
             public_id_path=public_id_path)
        # 3. 解压base.apk  获取AndroidManifest.xml 和res
        task(f"[{module_name}]-解压resources_apk", unzip_file, link_base_apk_path, unzip_link_apk_path)
        # 4. 修改AndroidManifest.xml 的 位置 构建aab需要的目录
        task(f"[{module_name}]-移动AndroidManifest", mv, temp_android_manifest_path, target_android_manifest_path)
        # 5. 拷贝assets
        if os.path.exists(input_assets):
            task(f"[{module_name}]-拷贝assets", copy, input_assets, target_assets_path)
        # 6. 拷贝lib
        if os.path.exists(input_lib):
            task(f"[{module_name}]-拷贝lib", copy, input_lib, target_lib_path)
        # 7. 拷贝其他的文件
        if os.path.exists(input_unknown):
            task(f"[{module_name}]-拷贝unknown", copy, input_unknown, target_unknown_path)
        # 8. 拷贝kotlin的文件
        if os.path.exists(input_kotlin):
            task(f"[{module_name}]-拷贝kotlin", copy, input_kotlin, target_kotlin_path)
        # 9. 删除apk的签名信息
        if os.path.exists(input_meta_inf_path):
            task(f"[{module_name}]-处理原有的apk签名信息", delete_sign, input_meta_inf_path)
        # 10. 拷贝META-INF的时候需要先删除 apk的签名信息
        if os.path.exists(input_meta_inf_path):
            task(f"[{module_name}]-拷贝META-INF", copy, input_meta_inf_path, target_mata_inf_path)
        # 11. 拷贝 dex
        if os.path.exists(input_resources_dir):
            task(f"[{module_name}]-拷贝dex", copy_dex, input_resources_dir, target_dex_path)
        # 12. 压缩成base.zip
        task(f"[{module_name}]-压缩zip", zip_file, unzip_link_apk_path, out_module_zip_path)
        return 0, "success"

    def run(self, apk_path, out_aab_path, pad_reg=""):
        self.pad_reg = pad_reg

        # 生成临时的工作目录
        temp_dir = f"temp_{'{0:%Y%m%d%H%M%S}'.format(datetime.datetime.now())}"
        if os.path.exists(temp_dir):
            delete(temp_dir)
        os.mkdir(temp_dir)

        module_zip_dir = os.path.join(temp_dir, "modules")
        module_asset_pack_dir = os.path.join(temp_dir, "asset_pack")
        os.mkdir(module_zip_dir)
        os.mkdir(module_asset_pack_dir)

        decode_apk_dir = os.path.join(temp_dir, "decode_apk_dir")

        temp_aab_path = os.path.join(temp_dir, "base.aab")

        # 添加模块
        self.bundle_modules["base"] = decode_apk_dir

        public_id_path = os.path.join(temp_dir, "public.txt")

        try:
            task("环境&参数校验", self.check_system, apk_path, out_aab_path)
            task("解压input_apk", decode_apk, apk_path, decode_apk_dir, self.apktool)
            task("解析apk信息", self.analysis_apk, decode_apk_dir)
            task("构建public.txt", self.build_public_id, public_id_path, decode_apk_dir)
            if self.is_pad():
                module_name = "pad_sy"
                pad_module_temp_dir = os.path.join(temp_dir, module_name)
                package = self.apk_package_name
                task("构建一个pad模块", create_pad_module_dir, pad_module_temp_dir, module_name, package)
                task("移动资源到pad模块", pad_mv_assets, decode_apk_dir, pad_module_temp_dir, self.pad_reg)
                self.bundle_asset_pack_modules[module_name] = pad_module_temp_dir

            for name, path in self.bundle_modules.items():
                task(f"[{name}]-构建module压缩包", self.build_module_zip, temp_dir, name, path,
                     os.path.join(module_zip_dir, name + ".zip"), public_id_path)

            for name, path in self.bundle_asset_pack_modules.items():
                task(f"[{name}]-构建asset_pack_module", self.build_asset_pack, temp_dir, name, path,
                     os.path.join(module_asset_pack_dir, name + ".zip"))
            # 获取所有的module 的name
            all_module_name = self.bundle_modules.keys()
            # 获取所有module的path
            all_module_path = list(map(lambda x: os.path.join(module_zip_dir, x + ".zip"), all_module_name))
            # 构建编译的module
            modules = ",".join(all_module_path)
            bundle_config_json_path = os.path.join(temp_dir, "BundleConfig.pb.json")
            task("构建config json", create_bundle_config_json, bundle_config_json_path, self.do_not_compress)
            task("构建aab", build_bundle, self.bundletool, modules, temp_aab_path, bundle_config_json_path)
            for name, path in self.bundle_asset_pack_modules.items():
                task(f"[{name}]-压缩asset_pack in aab", zip_file, path, temp_aab_path, name)
            task("签名", sign, temp_aab_path, self.keystore, self.storepass, self.keypass, self.alias)
            task("拷贝输出拷贝", copy, temp_aab_path, out_aab_path)
        except Exception as e:
            print_log(e)
            return -1, str(e)
        finally:
            pass
            status, _ = delete(temp_dir)
        return 0, "success"


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
    parser.add_argument(
        "--pad_reg", help="从Assets目录中提取pad资源，通过正则去匹配文件拷贝.", default="")
    args = parser.parse_args()

    input_apk_path = os.path.abspath(args.input)
    output_aab_path = os.path.abspath(args.output)
    keystore = args.keystore
    store_password = args.store_password
    key_alias = args.key_alias
    key_password = args.key_password
    input_apktool_path = args.apktool
    aapt2 = args.aapt2
    android = args.android
    bundletool = args.bundletool
    input_pad_reg = args.pad_reg

    bundletool = Bundletool(keystore=keystore,
                            storepass=store_password,
                            alias=key_alias,
                            keypass=key_password,
                            apktool=input_apktool_path,
                            aapt2=aapt2,
                            android=android,
                            bundletool=bundletool)
    status, message = bundletool.run(apk_path=input_apk_path,
                                     out_aab_path=output_aab_path,
                                     pad_reg=input_pad_reg)

    sys.exit(status)
pass
