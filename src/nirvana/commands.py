import warnings
import sys

from debianizer.writer import Debianizer
from reader import load_config, ConfigError, ConfigWarning

def _get_config():
    with warnings.catch_warnings(record=True) as warnings_list:
        warnings.simplefilter('always')
        try:
            config = load_config()
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