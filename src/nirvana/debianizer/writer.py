import os
from collections import defaultdict
import shutil

from utils import remove_debianization, get_current_datetime, create_file_path


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

        try:
            self._file = open(self._filename, 'w')
        except IOError:
            create_file_path(self._filename)
            self._file = open(self._filename, 'w')

        for line in self._lines:
            self._file.write(line + '\n')

        self._file.close()

        if self._executable:
            os.system('chmod a+x %s' % self._filename)

    def push(self, *lines):
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
                output.push(
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
                )

    def make_control(self):
        header_config = self.config.header
        with ConfigWriter('control') as output:

            python_version = header_config['python']['version']
            output.push(
                'Source: %s' % header_config['project']['name'],
                'Build-Depends: debhelper (>= 4), python (>=2.5), python-support, cdbs',
                'XS-Python-Version: >= 2.5',
                'Maintainer: %s <%s>' % (
                    header_config['project']['maintainer'],
                    header_config['project']['maintainer_email'],
                ),
            )

            for package_config in self.config.packages:
                output.push(
                    '',
                    'Package: %s' % package_config['package']['name'],
                    'Architecture: all',
                )
                requirements = ['Depends: python%s,' % ' (%s)' % python_version if python_version else '']

                if package_config['django']:
                    requirements.append(' python-django,')
                    requirements.append(' python-flup,')

                if package_config['django']['server'] == 'nginx':
                    requirements.append(' nginx,')

                requirements.extend(' %s,' % r for r in package_config['package']['debian-requirements'])

                # Remove last trailing comma
                requirements[-1] = requirements[-1][:-1]

                output.push(*requirements)

                output.push('XB-Python-Version: ${python:Versions}')
                output.push('Description: %s' % package_config['package']['description'])

    def make_rules(self):
        header_config = self.config.header
        with ConfigWriter('rules', executable=True) as output:
            output.push(
                '#!/usr/bin/make -f',
                '',
                'DEB_PYTHON_SYSTEM = pycentral',
                'DEB_COMPRESS_EXCLUDE = .py',
                '',
                'include /usr/share/cdbs/1/rules/debhelper.mk',
            )
            if header_config['python']:
                output.push('include /usr/share/cdbs/1/class/python-distutils.mk')

            sections = defaultdict(lambda: defaultdict(list))
            #for package in self.config.packages:
            #    package_name = package['package']['name']
            #    sections['binary-install'][package_name].append('dh_clearvcs -p%s' % package_name)

            for section_type, section_rules in sections.iteritems():
                for package_name, package_rules in section_rules.iteritems():
                    output.push('', '%s/%s::' % (section_type, package_name))
                    output.push('\t' + rule for rule in package_rules)

    def make_setup_py(self):
        header_config = self.config.header
        if not header_config['python']:
            return

        with ConfigWriter('/setup.py') as output:
            output.push(
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
            )

            if header_config['entry_points']:
                output.push(
                    '    entry_points={',
                    '        \'console_scripts\': [',
                )

                for key, value in header_config['entry_points']:
                    output.push('            %s,' % repr('%s = %s' % (key, value)))

                output.push(
                    '        ]',
                    '    },'
                )

            output.push(')')

    def _get_dirs(self, package_config, only_777=False):
        dirs = ['/var/log/%s' % package_config['package']['name']]

        dirs.extend('/var/spool/%s/%s' % (
            package_config['package']['name'], s
        ) for s in (package_config['dirs']['spool_777'] or '').split(',') if s)

        if not only_777:
            dirs.extend('/var/spool/%s/%s' % (
                package_config['package']['name'], s
            ) for s in (package_config['dirs']['spool'] or '').split(',') if s)

            if package_config['django']['server'] == 'nginx':
                dirs.append('/var/log/nginx/%s' % package_config['django']['project'])

        return dirs

    def make_dirs(self):
        for package_config in self.config.packages:
            with ConfigWriter('dirs', package=package_config, count=self.config.packages_count) as output:
                output.push(*self._get_dirs(package_config))

    def make_install(self):
        for package_config in self.config.packages:
            with ConfigWriter('install', package=package_config, count=self.config.packages_count) as output:

                if package_config['django']:
                    django_dir = package_config['django']['dir']
                    output.push('%s/*\t\t\t/usr/lib/%s' % (django_dir, django_dir))
                    output.push('debian/upstart/*\t\t\t/etc/init/')

                    if package_config['django']['server'] == 'nginx':
                        output.push('debian/nginx/*\t\t\t/etc/nginx/sites-available/')

    def make_postinst(self):
        for package_config in self.config.packages:
            if package_config['django']:

                django_project = package_config['django']['project']

                with ConfigWriter('postinst', executable=True, package=package_config, count=self.config.packages_count) as output:
                    output.push(
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
                    )

                    for d in self._get_dirs(package_config, only_777=True):
                        output.push('        chmod 777 %s' % d)

                    output.push(
                        '',
                        '        ln -fs /etc/nginx/sites-available/90-%s /etc/nginx/sites-enabled/90-%s' % (
                            django_project, django_project
                        ),
                        '        start %s || restart %s' % (django_project, django_project),
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
                    )

    def make_nginx(self):
        for package_config in self.config.packages:
            if package_config['django']['server'] == 'nginx':
                with ConfigWriter('nginx/90-%s' % package_config['django']['project'], executable=True,
                                  package=package_config, count=self.config.packages_count) as output:

                    # Main config
                    output.push(
                        'server {',
                        '    listen 80;',
                        '    server_name %s;' % package_config['django']['project'],
                        '',
                        '    access_log /var/log/nginx/%s/access.log;' % package_config['django']['project'],
                        '    error_log /var/log/nginx/%s/error.log;' % package_config['django']['project'],
                        '',
                        '    set $root /usr/lib/%s;' % package_config['django']['dir'],
                        '',
                        '    location / {',
                        '        fastcgi_pass unix:/var/run/nirvana/%s/fcgi.sock;' % package_config['django']['project'],
                        '        include /etc/nginx/fastcgi_params;',
                        '        fastcgi_param PATH_INFO $fastcgi_script_name;',
                        '        fastcgi_param SCRIPT_NAME \'\';',
                        '        client_max_body_size 30m;',
                        '    }',
                        '',
                        '    location ^~ /media/ {',
                        '        root $root;',
                        '    }',
                        '',
                        '    location ^~ /admin/media/ {',
                        '        root /usr/lib/python2.7/dist-packages/django/contrib/;',
                        '    }',
                        '',
                        '    location ~* ^/(robots\.txt|humans\.txt)$ {',
                        '        root $root;',
                        '    }',
                        '',
                        '    location = /favicon.ico {',
                        '        root $root/media/;',
                        '    }',
                    )

                    if package_config['django']['internal_redirect']:
                        relative_url, directory = package_config['django']['internal_redirect'].split(':')

                        output.push(
                            '',
                            '    location /%s {' % relative_url,
                            '        internal;',
                            '        alias /var/spool/%s/%s/;' % (package_config['package']['name'], directory),
                            '    }',
                        )

                    output.push('}')

                    # Redirect from www.
                    output.push(
                        '',
                        'server {',
                        '    listen 80;',
                        '    server_name www.%s;' % package_config['django']['project'],
                        '    rewrite ^(.*)$ http://%s/$1 permanent;' % package_config['django']['project'],
                        '}',
                    )

                    # Custom redirects
                    for redirect_from, redirect_to in package_config['redirect']:
                        output.push(
                            '',
                            'server {',
                            '    listen 80;',
                            '    server_name %s;' % redirect_from,
                        )

                        if redirect_to.endswith('/'):
                            output.push('    rewrite ^(.*)$ http://%s permanent;' % redirect_to)
                        else:
                            output.push('    rewrite ^(.*)$ http://%s/$1 permanent;' % redirect_to)

                        output.push('}')

    def make_django(self):
        for package_config in self.config.packages:
            if package_config['django']:
                var_run_dir = '/var/run/nirvana/%s/' % package_config['django']['project']
                with ConfigWriter('upstart/%s.conf' % package_config['django']['project']) as output:
                    output.push(
                        'description    "%s"' % package_config['django']['project'],
                        '',
                        'start on filesystem or runlevel [2345]',
                        'stop on runlevel [!2345]',
                        '',
                        'console none',
                        '',
                        'pre-start script',
                        '    mkdir -p %s' % var_run_dir,
                        '    chown -R www-data:www-data %s' % var_run_dir,
                        'end script',
                        '',
                        'pre-stop script',
                        '    kill -SIGINT `cat %sfcgi.pid`' % var_run_dir,
                        '    sleep 5',
                        'end script',
                        '',
                        (
                            'exec sudo -u www-data /usr/lib/%(dir)s/manage.py runfcgi ' +
                            'pidfile=%(var_run)sfcgi.pid ' +
                            'socket=%(var_run)sfcgi.sock ' +
                            'method=prefork ' +
                            'minspare=%(minspare)s ' +
                            'maxspare=%(maxspare)s ' +
                            'maxchildren=%(maxchildren)s ' +
                            'daemonize=false'
                        ) % {
                            'dir': package_config['django']['dir'],
                            'var_run': var_run_dir,
                            'minspare': package_config['django']['minspare'],
                            'maxspare': package_config['django']['maxspare'],
                            'maxchildren': package_config['django']['maxchildren'],
                        },
                    )

    def execute(self, version, changelog_filename=None):
        self.prepare()
        self._version = version
        for method_name in dir(self):
            if method_name.startswith('make_'):
                getattr(self, method_name)()
        self.copy_changelog(changelog_filename)
