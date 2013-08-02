import warnings
import sys
import re

from debianizer import Debianizer
from reader import load_config, ConfigError, ConfigWarning
from debianizer.utils import remove_debianization, remove_deb_package, remove_eggs
import settings
from utils import call_command


class Commands(object):
    @property
    def config(self):
        if not hasattr(self, '_config'):
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
                print ('Error: invalid changelog file')
                sys.exit(1)
            except IOError:
                self._version = '0.1.0'

        return self._version

    def command_debianize(self, args):
        """
        Create debianization for a project based on nirvana config files
        """

        Debianizer(self.config).execute(self.version)
        print('The debianization is ready')

    def command_clean(self, args, remove_deb=True):
        """
        Remove debian/, setup.py, build-related files
        """
        remove_debianization()
        for package_config in self.config.packages():
            package_name = package_config['package']['name']
            remove_eggs(package_name, self.config.header()['python']['source_dir'])
            if remove_deb:
                remove_deb_package(package_name, self.version)

        print('Clean completed')

    def command_changelog(self, args):
        """
        Create and update changelog
        """
        create = args and args[0] == '--create'

        if create:
            call_command('dch --create --distributor=nirvana --changelog changelog')
        else:
            call_command('dch -i --distributor=nirvana --changelog changelog')

    def command_build(self, args):
        """
        Make a deb-package
        """
        self.command_debianize(args)
        call_command('debuild')
        self.command_clean(args, remove_deb=False)

    def command_install(self, args):
        """
        Install the package in the system
        """

        self.command_debianize(args)
        call_command('debuild')
        for package_config in self.config.packages():
            call_command('sudo dpkg -i ../%s_%s_all.deb' % (
                package_config['package']['name'],
                self.version,
            ))
        self.command_clean(args)

commands = Commands()
