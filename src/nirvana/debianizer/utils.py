import os
import shutil
import datetime
import time
import subprocess

def remove_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def create_file_path(filename):
    path = os.path.split(filename)[0]
    subprocess.call(['mkdir', '-p', path])


def remove_debianization():
    remove_path('debian')
    remove_path('build')
    remove_path('setup.py')


def remove_deb_package(package_name, version):
    file_mask = '../%s_%s' % (package_name, version)
    remove_path(file_mask + '.dsc')
    remove_path(file_mask + '.tar.gz')
    remove_path(file_mask + '_all.deb')
    remove_path(file_mask + '_amd64.build')
    remove_path(file_mask + '_amd64.changes')
    remove_path(file_mask + '_amd64.upload')


def remove_eggs(package_name, source_dir):
    remove_path(os.path.join(source_dir, package_name.replace('-', '_') + '.egg-info'))


def get_current_datetime():
    """
    Get datetime in a changelog-compliant format.
    I.e.: Sun, 29 Apr 2012 23:06:46 +0400
    """
    # Not using .strftime because of various locales issues.

    tz_offset = -time.timezone // 60  # In minutes
    tz_offset_hours = tz_offset // 60
    tz_offset_minutes = tz_offset % 60
    tz_offset_string = '%s%02d%02d' % ('-' if tz_offset < 0 else '+', tz_offset_hours, tz_offset_minutes)

    now = datetime.datetime.now()
    return '%(day_of_week)s, %(day)s %(month)s %(year)s %(time)s %(timeshift)s' % {
        'day_of_week': ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')[now.weekday()],
        'day': now.day,
        'month': ('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Nov', 'Oct', 'Dec')[now.month],
        'year': now.year,
        'time': now.strftime('%H:%M:%S'),
        'timeshift': tz_offset_string,
    }
