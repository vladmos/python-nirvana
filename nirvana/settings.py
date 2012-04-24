DEFAULT_FILENAME = 'nirvana.ini'

CONFIG_STRUCTURE = {
    'package': {
        'required': True,
        'fields': ['name', 'maintainer', 'maintainer_email', 'requirements', 'description'],
    },
    'python': {
        'fields': ['version', 'source_dir'],
    },
    'django': {
        'requires': [('nginx', 'lighttpd')],
        'fields': ['project'],
        'optional': ['ycssjs'],
    },
    'nginx': {
        'requires': ['django'],
        'fields': ['server_name'],
        'optional': ['client_max_body_size', 'include', 'rewrite', 'internal'],
    },
    'cron': {
        'custom': True,
    },
    'dirs': {
        'optional': ['spool'],
    },
}