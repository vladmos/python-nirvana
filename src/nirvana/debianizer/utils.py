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
