DEFAULT_CONFIG_FILENAME = 'nirvana.ini'
CHANGELOG_FILENAME = 'changelog'

HEADER_CONFIG_STRUCTURE = {
    'project': {
        'required': True,
        'fields': ['name', 'description', 'maintainer', 'maintainer_email'],
    },
    'python': {
        'fields': ['version', 'source_dir'],
    },
    'entry_points': {
        'requires': ['python'],
        'custom': True,
    }
}

PACKAGE_CONFIG_STRUCTURE = {
    'package': {
        'required': True,
        'fields': ['name', 'description'],
        'optional': ['debian-requirements', 'logs'],
        'load_file': ['debian-requirements'],
    },
    'django': {
        'fields': ['server', 'project', 'minspare', 'maxspare', 'maxchildren', 'dir'],
        'optional': ['ycssjs', 'internal_redirect', 'alias', 'ssl'],
    },
    'redirect': {
        'requires': ['django'],
        'custom': True,
    },
    'cron': {
        'custom': True,
    },
    'dirs': {
        'optional': ['spool', 'spool_777'],
    },
}

SINGLE_CONFIG_STRUCTURE = HEADER_CONFIG_STRUCTURE.copy()
SINGLE_CONFIG_STRUCTURE.update(PACKAGE_CONFIG_STRUCTURE)
