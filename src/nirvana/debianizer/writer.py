import os
from collections import defaultdict

from utils import remove_path, remove_debianization

class ConfigWriter(object):
    def __init__(self, filename):
        self._filename = filename[1:] if filename.startswith('/') else 'debian/' + filename

    def __enter__(self):
        self._file = open(self._filename, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def push(self, lines):
        if isinstance(lines, basestring):
            lines = [lines]
        else:
            lines = list(lines)

        for line in lines:
            self._file.write(line + '\n')


class Debianizer(object):
    def __init__(self, config):
        self.config = config

    def prepare(self):
        remove_debianization()
        os.makedirs('debian')

    def make_control(self):
        header_config = self.config.header()
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

            for package_config in self.config.packages():
                output.push([
                    '',
                    'Package: %s' % package_config['package']['name'],
                    'Architecture: all',
                ])
                requirements = ['Depends: python%s,' % ' (%s)' % python_version if python_version else '']
                requirements.extend(' %s,' % r for r in package_config['package']['debian-requirements'])

                #Remove last trailing comma
                requirements[-1] = requirements[-1][:-1]

                output.push(requirements)

                output.push('Description: %s' % package_config['package']['description'])

    def make_rules(self):
        header_config = self.config.header()
        with ConfigWriter('rules') as output:
            output.push([
                '#!/usr/bin/make -f',
                '',
                'include /usr/share/cdbs/1/rules/debhelper.mk',
            ])
            if header_config['python']:
                output.push('include /usr/share/cdbs/1/class/python-distutils.mk')

            sections = defaultdict(lambda: defaultdict(list))
            for package in self.config.packages():
                package_name = package['package']['name']
                sections['binary-install'][package_name].append('dh_clearvcs -p%s' % package_name)

            for section_type, section_rules in sections.iteritems():
                for package_name, package_rules in section_rules.iteritems():
                    output.push(['', '%s/%s' % (section_type, package_name)])
                    output.push('\t' + rule for rule in package_rules)

    def make_setup_py(self):
        header_config = self.config.header()
        if not header_config['python']:
            return

        with ConfigWriter('/setup.py') as output:
            output.push([
                'from setuptools import setup, find_packages',
                '',
                'setup(',
                '    name=%s,' % repr(header_config['project']['name']),
                '    version=0.1,',
                '    description=%s,' % repr(header_config['project']['description']),
                '    author=%s,' % repr(header_config['project']['maintainer']),
                '    author_email=%s,' % repr(header_config['project']['maintainer_email']),
                '    package_dir={\'\': %s},' % repr(header_config['python']['source_dir']),
                '    packages=find_packages(%s),' % repr(header_config['python']['source_dir']),
                ')'
            ])

    def execute(self):
        self.prepare()
        for method_name in dir(self):
            if method_name.startswith('make_'):
                getattr(self, method_name)()
