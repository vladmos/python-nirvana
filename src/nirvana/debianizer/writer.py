import os
from collections import defaultdict
import shutil

from utils import remove_debianization, get_current_datetime


class ConfigWriter(object):
    def __init__(self, filename, executable=False, package=None, count=1):
        if package and count > 1:
            filename = '%s.%s' % (package['package']['name'], filename)
        self._filename = filename[1:] if filename.startswith('/') else 'debian/' + filename
        self._executable = executable
        self._lines = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._lines:
            return

        self._file = open(self._filename, 'w')

        for line in self._lines:
            self._file.write(line + '\n')

        self._file.close()

        if self._executable:
            os.system('chmod a+x %s' % self._filename)

    def push(self, lines):
        if isinstance(lines, basestring):
            lines = [lines]

        self._lines.extend(lines)


class Debianizer(object):
    def __init__(self, config):
        self.config = config

    def prepare(self):
        remove_debianization()
        os.makedirs('debian')

    def copy_changelog(self, changelog_filename):
        if changelog_filename:
            shutil.copyfile(changelog_filename, 'debian/changelog')
        else:
            with ConfigWriter('changelog') as output:
                header_config = self.config.header
                output.push([
                    '%(project_name)s (%(version)s) unstable; urgency=low' % {
                        'project_name': header_config['project']['name'],
                        'version': self._version,
                    },
                    '',
                    '  * Initial release.',
                    '',
                    ' -- %(maintainer_name)s <%(maintainer_email)s>  %(datetime)s' % {
                        'maintainer_name': header_config['project']['maintainer'],
                        'maintainer_email': header_config['project']['maintainer_email'],
                        'datetime': get_current_datetime(),
                    },
                ])

    def make_control(self):
        header_config = self.config.header
        with ConfigWriter('control') as output:

            python_version = header_config['python']['version']
            output.push([
                'Source: %s' % header_config['project']['name'],
                'Build-Depends: debhelper (>= 4), python (>=2.5), python-support, cdbs',
                'XS-Python-Version: >= 2.5',
                'Maintainer: %s <%s>' % (
                    header_config['project']['maintainer'],
                    header_config['project']['maintainer_email'],
                ),
            ])

            for package_config in self.config.packages:
                output.push([
                    '',
                    'Package: %s' % package_config['package']['name'],
                    'Architecture: all',
                ])
                requirements = ['Depends: python%s,' % ' (%s)' % python_version if python_version else '']

                if package_config['django']:
                    requirements.append(' python-django,')
                    requirements.append(' python-flup,')

                if package_config['nginx']:
                    requirements.append(' nginx,')

                requirements.extend(' %s,' % r for r in package_config['package']['debian-requirements'])

                # Remove last trailing comma
                requirements[-1] = requirements[-1][:-1]

                output.push(requirements)

                output.push('XB-Python-Version: ${python:Versions}')
                output.push('Description: %s' % package_config['package']['description'])

    def make_rules(self):
        header_config = self.config.header
        with ConfigWriter('rules', executable=True) as output:
            output.push([
                '#!/usr/bin/make -f',
                '',
                'DEB_PYTHON_SYSTEM = pycentral',
                'DEB_COMPRESS_EXCLUDE = .py',
                '',
                'include /usr/share/cdbs/1/rules/debhelper.mk',
            ])
            if header_config['python']:
                output.push('include /usr/share/cdbs/1/class/python-distutils.mk')

            sections = defaultdict(lambda: defaultdict(list))
            #for package in self.config.packages:
            #    package_name = package['package']['name']
            #    sections['binary-install'][package_name].append('dh_clearvcs -p%s' % package_name)

            for section_type, section_rules in sections.iteritems():
                for package_name, package_rules in section_rules.iteritems():
                    output.push(['', '%s/%s::' % (section_type, package_name)])
                    output.push('\t' + rule for rule in package_rules)

    def make_setup_py(self):
        header_config = self.config.header
        if not header_config['python']:
            return

        with ConfigWriter('/setup.py') as output:
            output.push([
                'from setuptools import setup, find_packages',
                '',
                'setup(',
                '    name=%s,' % repr(header_config['project']['name']),
                '    version=%s,' % repr(self._version),
                '    description=%s,' % repr(header_config['project']['description']),
                '    author=%s,' % repr(header_config['project']['maintainer']),
                '    author_email=%s,' % repr(header_config['project']['maintainer_email']),
                '    package_dir={\'\': %s},' % repr(header_config['python']['source_dir']),
                '    packages=find_packages(%s),' % repr(header_config['python']['source_dir']),
            ])

            if header_config['entry_points']:
                output.push([
                    '    entry_points={',
                    '        \'console_scripts\': [',
                ])

                for key, value in header_config['entry_points']:
                    output.push('            %s,' % repr('%s = %s' % (key, value)))

                output.push([
                    '        ]',
                    '    },'
                ])

            output.push(')')

    def _get_dirs(self, package_config, only_777=False):
        dirs = []

        dirs.extend('/var/spool/%s/%s' % (
            package_config['package']['name'], s
        ) for s in package_config['dirs']['spool_777'].split(','))

        if not only_777:
            dirs.extend('/var/spool/%s/%s' % (
                package_config['package']['name'], s
            ) for s in package_config['dirs']['spool'].split(','))

            if package_config['nginx']:
                dirs.append('/var/log/nginx/%s' % package_config['django']['project'])

        return dirs

    def make_dirs(self):
        for package_config in self.config.packages:
            with ConfigWriter('dirs', package=package_config, count=self.config.packages_count) as output:
                output.push(self._get_dirs(package_config))

    def make_install(self):
        for package_config in self.config.packages:
            with ConfigWriter('install', package=package_config, count=self.config.packages_count) as output:

                if package_config['django']:
                    django_dir = package_config['django']['dir']
                    output.push('%s/*\t\t\t/usr/lib/%s' % (django_dir, django_dir))
                    output.push('debian/%s.conf\t\t\t/etc/init/' % package_config['django']['project'])

                if package_config['nginx']:
                    output.push('debian/90-%s\t\t\t/etc/nginx/sites-available/' % package_config['django']['project'])

    def make_postinst(self):
        for package_config in self.config.packages:

            django_project = package_config['django']['project']

            with ConfigWriter('postinst', executable=True, package=package_config, count=self.config.packages_count) as output:
                output.push([
                    '#!/bin/bash',
                    'set -e',
                    '',
                    'USER="www-data"',
                    'GROUP="www-data"',
                    'DIRS=( %s )' % ' '.join('"%s"' % d for d in self._get_dirs(package_config)),
                    '',
                    'case $1 in',
                    '   configure)',
                    '        for DIR in ${DIRS[@]}; do',
                    '            chown -R $USER:$GROUP $DIR',
                    '        done',
                    '',
                ])
                output.push('        chmod 777 %s' % d for d in self._get_dirs(package_config, only_777=True))
                output.push([
                    '',
                    '        ln -s /etc/nginx/sites-available/90-%s /etc/nginx/sites-enabled/90-%s' % (
                        django_project, django_project
                    ),
                    '        /etc/init.d/nginx reload',
                    '',
                    '        ;;',
                    '',
                    '    abort-upgrade|abort-remove|abort-deconfigure)',
                    '        ;;',
                    '',
                    '    *)',
                    '        echo "postinst called with unknown argument \`$1\'" >&2',
                    '        ;;',
                    'esac',
                    '#DEBHELPER#',
                    'exit 0',
                ])


    def execute(self, version, changelog_filename=None):
        self.prepare()
        self._version = version
        for method_name in dir(self):
            if method_name.startswith('make_'):
                getattr(self, method_name)()
        self.copy_changelog(changelog_filename)
