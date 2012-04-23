import warnings
import sys

from debianizer.writer import Debianizer
from reader import Config, ConfigError, ConfigWarning
from settings import CONFIG_STRUCTURE

def _get_config(filename=None):
    with warnings.catch_warnings(record=True) as warnings_list:
        warnings.simplefilter('always')
        try:
            config = Config(structure=CONFIG_STRUCTURE, filename=filename)
        except ConfigError, e:
            print 'Nirvana configuration error: %s' % e
            sys.exit(1)

        for warning in warnings_list:
            if issubclass(warning.category, ConfigWarning):
                print 'Nirvana configuration warning: %s' % warning.message
        return config

def debianize():
    config = _get_config()
    Debianizer(config).execute()