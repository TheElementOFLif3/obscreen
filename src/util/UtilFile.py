import os
import uuid
import math
import shutil


def randomize_filename(old_filename: str) -> str:
    new_uuid = str(uuid.uuid4())
    _, extension = os.path.splitext(old_filename)
    return f"{new_uuid}{extension}"


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def copy_files(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)

    for root, dirs, files in os.walk(src):
        # Construct the destination path
        dst_path = os.path.join(dst, os.path.relpath(root, src))
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)

        for file in files:
            # Copy each file to the destination
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_path, file)
            shutil.copy2(src_file, dst_file)
