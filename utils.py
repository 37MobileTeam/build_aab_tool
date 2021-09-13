# coding=utf-8
"""
Copyright (C) 2021 37手游安卓团队

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import shutil
import zipfile
import platform

WINDOWS = "Windows"
Linux = "Linux"
MACOS = "Darwin"


def get_system() -> str:
    return platform.system()


def execute_cmd(cmd):
    # print("#" * 10, cmd)
    status = os.system(cmd)
    return status, ""


def read_file_text(file_path) -> str:
    with open(file_path, "r", encoding="UTF-8") as f:
        return f.read()


def write_file_text(file_path, text) -> int:
    with open(file_path, "w", encoding="UTF-8") as f:
        return f.write(text)


def get_file_name_list(file_dir: str):
    file_dir = file_dir.replace("\\", "/")
    file_name_list = []
    for root, dirs, files in os.walk(file_dir):
        for f in files:
            file_name_list.append(os.path.join(root, f).replace(
                "\\", "/").replace(file_dir, ""))
    return file_name_list


def zip_file(src_dir, zip_name="", parent_dir_name=""):
    if not zip_name:
        zip_name = src_dir + '.zip'
    mode = "w"
    if os.path.exists(zip_name):
        mode = "a"
    if "w" == mode and parent_dir_name == "":
        # 尝试调用一下系统的压缩方法，  速度快一点。。。
        cmd = f"cd {src_dir} && zip -r -q -D {os.path.abspath(zip_name)} *"
        status, message = execute_cmd(cmd)
        if status == 0:
            return 0, "success",
        # 如果失败了，尝试去删除一下
        delete(zip_name)
    z = zipfile.ZipFile(zip_name, mode, zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(src_dir):
        fpath = dirpath.replace(src_dir, parent_dir_name)
        fpath = fpath and fpath + os.sep or ''
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath + filename)
    z.close()
    return 0, "success"


def unzip_file(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        return -1, "This is not zip"
    return 0, "success"


def mv(src_path, dst_path):
    # TODO 可以有优化
    copy(src_path, dst_path)
    delete(src_path)
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
