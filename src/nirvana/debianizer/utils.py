import os
import shutil


def remove_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def remove_debianization():
    remove_path('debian')
    remove_path('setup.py')


def remove_deb_package(package_name, version):
    file_mask = '../%s_%s' % (package_name, version)
    remove_path(file_mask + '.dsc')
    remove_path(file_mask + '.tar.gz')
    remove_path(file_mask + '_all.deb')
    remove_path(file_mask + '_amd64.build')
    remove_path(file_mask + '_amd64.changes')
    remove_path(file_mask + '_amd64.upload')
