import warnings

from ConfigParser import RawConfigParser, NoSectionError, NoOptionError

import settings

class ConfigError(Exception):
    pass

class ConfigWarning(Warning):
    pass


class IniConfigSection(object):
    def __init__(self, config, section):
        self._config = config
        self._section = section

    def __getitem__(self, item):
        try:
            return self._config.get(self._section, item)
        except (NoOptionError, NoSectionError):
            pass

    def __iter__(self):
        return iter(self._config.items(self._section))

    def __bool__(self):
        return bool(self._config.items(self._section))


class IniConfig(object):
    def __init__(self, filename, structure=None):
        self._config = RawConfigParser()
        if not self._config.read(filename):
            raise ConfigError(u'Config "%s" is missing' % filename)

        if structure is not None:
            self._check_structure(structure)

    def __getitem__(self, item):
        return IniConfigSection(self._config, item)

    def _check_structure(self, structure):
        """
        Checks whether the config is valid
        Raises the ConfigError exception or warnings
        """
        def plural(word, objects):
            if len(objects) > 1:
                return word + u's'
            return word

        def join(objects, brackets):
            return u', '.join(u'%s%s%s' % (brackets[0], o, brackets[-1]) for o in objects)

        config = self._config
        known_sections = set()
        for section, parameters in structure.iteritems():
            known_sections.add(section)

            # required
            if parameters.get('required') and not config.has_section(section):
                raise ConfigError(u'Missing required section [%s]' % section)

            if config.has_section(section):
                # fields
                for field in parameters.get('fields', []):
                     if not config.has_option(section, field):
                        raise ConfigError(u'Missing required field in the section [%s]: "%s"' % (section, field))

                # custom, optional
                if not parameters.get('custom') and config.has_section(section):
                    known_fields = set(parameters.get('optional', []) + parameters.get('fields', []))
                    unknown_fields = []
                    for field in config.options(section):
                        if field not in known_fields:
                            unknown_fields.append(field)
                    if unknown_fields:
                        warnings.warn(u'Unknown %s in the section [%s]: %s' % (
                            plural(u'field', unknown_fields),
                            section,
                            join(unknown_fields, u'"')), ConfigWarning)

                # requires
                if parameters.get('requires'):
                    for required_sections in parameters['requires']:
                        if type(required_sections) is not tuple:
                            required_sections = (required_sections,)
                        if all(not config.has_section(s) for s in required_sections):
                            raise ConfigError(u'Section [%s] requires %s %s' % (
                                section,
                                plural(u'section', required_sections),
                                join(required_sections, u'[]')))

        unknown_sections = []
        for section in config.sections():
            if section not in known_sections:
                unknown_sections.append(section)
        if unknown_sections:
            warnings.warn(u'Unknown %s %s' % (
                plural(u'section', unknown_sections),
                join(unknown_sections, u'[]')), ConfigWarning)


class Config(object):
    pass


class SingleConfig(Config):
    def __init__(self, filename):
        self._main_config = IniConfig(filename, structure=settings.SINGLE_CONFIG_STRUCTURE)

    def header(self):
        return self._main_config

    def packages(self):
        return [self._main_config]


class MultipleConfig(Config):
    def __init__(self, header_filename, package_filenames):
        self._header_config = IniConfig(header_filename, structure=settings.HEADER_CONFIG_STRUCTURE)
        self._package_configs = [IniConfig(f, settings.PACKAGE_CONFIG_STRUCTURE) for f in package_filenames]

    def header(self):
        return self._header_config

    def packages(self):
        return self._package_configs


def load_config():
    return SingleConfig(settings.DEFAULT_CONFIG_FILENAME)