import os
from collections import defaultdict

from utils import remove_path

class Debianizer(object):
    def __init__(self, config):
        self.config = config
        self.name = self.config['package']['name']

    def prepare(self):
        remove_path('debian')
        remove_path('setup.py')
        os.makedirs('debian')

    def _make_config(self, filename, lines):
        filename = filename[1:] if filename.startswith('/') else 'debian/' + filename

        with open(filename, 'w') as file:
            file.write('\n'.join(lines))
            file.write('\n')

    def make_control(self):
        python_version = self.config['python']['version']
        lines = [
            'Source: %s' % self.name,
            'Build-Depends: debhelper (>= 4), python (>=2.5), python-support, cdbs',
            'XS-Python-Version: >= 2.5',
            'Maintainer: %s <%s>' % (
                self.config['package']['maintainer'],
                self.config['package']['maintainer_email'],
            ),
            '',
            'Package: %s' % self.name,
            'Architecture: all',
            'Depends: python%s,' % ' (%s)' % python_version if python_version else '',
        ]

        #Remove last trailing comma
        lines[-1] = lines[-1][:-1]

        lines.append('Description: %s' % self.config['package']['description'])

        self._make_config('control', lines)

    def make_rules(self):
        lines = [
            '#!/usr/bin/make -f',
            '',
            'include /usr/share/cdbs/1/rules/debhelper.mk',
        ]
        if self.config['python']:
            lines.append('include /usr/share/cdbs/1/class/python-distutils.mk')

        sections = defaultdict(lambda: defaultdict(list))
        sections['binary-install'][self.name].append('dh_clearvcs -p%s' % self.name)

        for section_type, section_rules in sections.iteritems():
            for package_name, package_rules in section_rules.iteritems():
                lines.extend(['', '%s/%s' % (section_type, package_name)])
                lines.extend('\t' + rule for rule in package_rules)

        self._make_config('rules', lines)

    def make_setup_py(self):
        if not self.config['python']:
            return

        lines = [
            'from setuptools import setup, find_packages',
            '',
            'setup(',
            '    name=%s,' % repr(self.name),
            '    version=0.1,',
            '    description=%s,' % repr(self.config['package']['description']),
            '    author=%s,' % repr(self.config['package']['maintainer']),
            '    author_email=%s,' % repr(self.config['package']['maintainer_email']),
            '    package_dir={\'\': %s},' % repr(self.config['python']['source_dir']),
            '    packages=find_packages(%s),' % repr(self.config['python']['source_dir']),
            ')'
        ]

        self._make_config('/setup.py', lines)

    def execute(self):
        self.prepare()
        for method_name in dir(self):
            if method_name.startswith('make_'):
                getattr(self, method_name)()
