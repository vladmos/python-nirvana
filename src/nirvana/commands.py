import warnings
import sys
import os
import re

from debianizer.writer import Debianizer
from reader import load_config, ConfigError, ConfigWarning
from debianizer.utils import remove_debianization
import settings

def _get_config():
    with warnings.catch_warnings(record=True) as warnings_list:
        warnings.simplefilter('always')
        try:
            config = load_config()
        except ConfigError, e:
            print('Nirvana configuration error: %s' % e)
            sys.exit(1)

        for warning in warnings_list:
            if issubclass(warning.category, ConfigWarning):
                print('Nirvana configuration warning: %s' % warning.message)
        return config

def debianize():
    config = _get_config()

    try:
        with open(settings.CHANGELOG_FILENAME) as changelog_file:
            line = changelog_file.readline()
            version = re.search(r'\((.*?)\)', line).group(1)
    except (IOError, AttributeError):
        print ('Error: missing or invalid changelog file')
        sys.exit(1)

    Debianizer(config).execute(version, settings.CHANGELOG_FILENAME)
    print('The debianization is ready')

def clean():
    remove_debianization()
    print('The debianization is deleted')

def changelog(create=False):
    if create:
        os.system('dch --create --distributor=yandex --changelog changelog')
    else:
        os.system('dch -i --distributor=yandex --changelog changelog')
