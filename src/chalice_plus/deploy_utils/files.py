import errno
import os
import shutil

from functools import cache
from pathlib import Path


LAMBDA_FILES = (
    "__init__.py",
    "authenticators.py",
    "exceptions.py",
    "masking.py",
    "permissions.py",
    "urls.py",
    "views.py",
)


def delete_path(path):
    shutil.rmtree(path)


def delete_path_if_empty(path):
    if len(os.listdir(path)) == 0:
        delete_path(path)


def delete_path_if_exists(path):
    if os.path.exists(path):
        delete_path(path)


def copy_path(src, dest):
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
    except OSError as e:
        if e.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dest)
        else:
            raise


@cache
def get_vendor_src():
    return Path(__file__).resolve().parent.parent


@cache
def get_vendor_dest():
    return os.path.join(os.getcwd(), "vendor", "chalice_plus")


def copy_chalice_plus_vendor_folder():
    vendor_src = get_vendor_src()
    vendor_dest = get_vendor_dest()

    delete_path_if_exists(vendor_dest)
    os.makedirs(vendor_dest)

    for filename in LAMBDA_FILES:
        copy_path(os.path.join(vendor_src, filename), vendor_dest)


def remove_chalice_plus_vendor_folder():
    vendor_dest = get_vendor_dest()
    delete_path_if_exists(vendor_dest)
    delete_path_if_empty(Path(vendor_dest).resolve().parent)
