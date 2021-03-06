from __future__ import print_function

import warnings
import sys
import re

from debianizer import Debianizer
from reader import load_config, ConfigError, ConfigWarning
from debianizer.utils import remove_debianization, remove_deb_package, remove_eggs
import settings
from utils import call_command


def pretty_print(message, error=False):
    """
    Prints the message in bold cyan font to distinguish messages from Nirvana
    """
    code = '31' if error else '36'
    print('\033[1;%sm%s\033[1;m' % (code, message))


class Commands(object):
    @property
    def config(self):
        if not hasattr(self, '_config'):
            with warnings.catch_warnings(record=True) as warnings_list:
                warnings.simplefilter('always')
                try:
                    config = load_config()
                except ConfigError, e:
                    pretty_print('Nirvana configuration error: %s' % e, error=True)
                    sys.exit(1)

                for warning in warnings_list:
                    if issubclass(warning.category, ConfigWarning):
                        pretty_print('Nirvana configuration warning: %s' % warning.message, error=True)

                self._config = config

        return self._config

    @property
    def version(self):
        if not hasattr(self, '_version'):
            try:
                with open(settings.CHANGELOG_FILENAME) as changelog_file:
                    line = changelog_file.readline()
                    self._version = re.search(r'\((.*?)\)', line).group(1)
            except AttributeError:
                pretty_print('Error: invalid changelog file', error=True)
                sys.exit(1)
            except IOError:
                self._version = '0.1.0'

        return self._version

    def command_debianize(self, args):
        """
        Create debianization for a project based on nirvana config files
        """

        pretty_print('Preparing debianization...')
        Debianizer(self.config).execute(self.version)

    def command_clean(self, args, remove_deb=True):
        """
        Remove debian/, setup.py, build-related files
        """
        pretty_print('Cleaning...')
        remove_debianization()
        for package_config in self.config.packages:
            package_name = package_config['package']['name']
            remove_eggs(package_name, self.config.header['python']['source_dir'])
            if remove_deb:
                remove_deb_package(package_name, self.version)

    def command_changelog(self, args):
        """
        Create and update changelog
        """
        pretty_print('Generating changelog...')
        create = args and args[0] == '--create'

        if create:
            call_command('dch --create --distributor=nirvana --changelog changelog')
        else:
            call_command('dch -i --distributor=nirvana --changelog changelog')

    def command_build(self, args, clean=True):
        """
        Make a deb-package
        """
        self.command_debianize(args)

        pretty_print('Building a debian package...')
        call_command('debuild -uc -us')

        if clean:
            self.command_clean(args, remove_deb=False)

    def command_install(self, args):
        """
        Install the package in the system
        """
        self.command_build(args, clean=False)

        pretty_print('Installing the package...')
        for package_config in self.config.packages:
            call_command('sudo dpkg -i ../%s_%s_all.deb' % (
                package_config['package']['name'],
                self.version,
            ))
        self.command_clean(args)

commands = Commands()
