import unittest
from shutil import copyfile
import os
import warnings

from context import nirvana
from nirvana import reader

CONFIG_FILENAME = 'test-nirvana.ini'

def prepare_config_file(sample_name, filename=CONFIG_FILENAME):
    copyfile('test_configs/%s.ini' % sample_name, filename)

class IniConfigReaderTester(unittest.TestCase):
    config_structure = {
        'required': {
            'required': True,
            'fields': ['required1', 'required2'],
            'optional': ['optional1', 'optional2'],
            },
        'optional': {
            'optional': ['optional1', 'optional2'],
            },
        'custom': {
            'custom': True
        }
    }

    def tearDown(self):
        os.system('rm -f *.ini')

    def test_blank_structure(self):
        prepare_config_file('sample')
        reader.IniConfig(CONFIG_FILENAME)

    def test_basic_verification(self):
        prepare_config_file('sample')
        reader.IniConfig(CONFIG_FILENAME, structure=self.config_structure)

    def test_optional_section(self):
        prepare_config_file('sample')
        config_structure = self.config_structure.copy()

        config_structure['section'] = {
            'fields': ['field'],
        }
        reader.IniConfig(CONFIG_FILENAME, structure=config_structure)

    def test_missing_required_field(self):
        prepare_config_file('no_required_parameter')
        self.assertRaises(reader.ConfigError, reader.IniConfig, CONFIG_FILENAME, structure=self.config_structure)

    def test_missing_required_section(self):
        prepare_config_file('no_required_section')
        self.assertRaises(reader.ConfigError, reader.IniConfig, CONFIG_FILENAME, structure=self.config_structure)

    def test_missing_config(self):
        self.assertRaises(reader.ConfigError, reader.IniConfig, CONFIG_FILENAME)

    def test_satisfied_requirements_1(self):
        prepare_config_file('requirements')
        config_structure = {
            'section1': {
                'requires': [('section2', 'section3'), 'section4'],
                'optional': ['key'],
            },
            'section2': {
                'optional': ['key'],
            },
            'section3': {
                'optional': ['key'],
            },
            'section4': {
                'optional': ['key'],
            },
        }
        reader.IniConfig(CONFIG_FILENAME, config_structure)

    def test_satisfied_requirements_2(self):
        prepare_config_file('requirements')
        config_structure = {
            'section1': {
                'requires': [('section2', 'missing_section'), 'section4'],
                'optional': ['key'],
            },
            'section2': {
                'optional': ['key'],
            },
            'section3': {
                'optional': ['key'],
            },
            'section4': {
                'optional': ['key'],
            },
        }
        reader.IniConfig(CONFIG_FILENAME, config_structure)

    def test_satisfied_requirements_3(self):
        prepare_config_file('requirements')
        config_structure = {
            'section1': {
                'optional': ['key'],
            },
            'section2': {
                'optional': ['key'],
            },
            'section3': {
                'optional': ['key'],
            },
            'section4': {
                'optional': ['key'],
            },
            'section5': {
                'requires': ['section6']
            },
        }
        reader.IniConfig(CONFIG_FILENAME, config_structure)



    def test_unsatisfied_requirements_1(self):
        prepare_config_file('requirements')
        config_structure = {
            'section1': {
                'requires': [('section2', 'section3'), 'missing_section'],
                'optional': ['key'],
            },
            'section2': {
                'optional': ['key'],
            },
            'section3': {
                'optional': ['key'],
            },
            'section4': {
                'optional': ['key'],
            },
        }
        self.assertRaises(reader.ConfigError, reader.IniConfig, CONFIG_FILENAME, structure=config_structure)

    def test_unsatisfied_requirements_2(self):
        prepare_config_file('requirements')
        config_structure = {
            'section1': {
                'requires': [('missing_section1', 'missing_section2'), 'section4'],
                'optional': ['key'],
            },
            'section2': {
                'optional': ['key'],
            },
            'section3': {
                'optional': ['key'],
            },
            'section4': {
                'optional': ['key'],
            },
        }
        self.assertRaises(reader.ConfigError, reader.IniConfig, CONFIG_FILENAME, structure=config_structure)

    def test_custom_sections(self):
        prepare_config_file('custom')
        config_structure = {
            'section': {
                'custom': True
            }
        }
        reader.IniConfig(CONFIG_FILENAME, config_structure)

    def test_unknown_field_warning(self):
        prepare_config_file('warnings')
        config_structure = {
            'section': {}
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            reader.IniConfig(CONFIG_FILENAME, config_structure)
            self.assertEqual(len(w), 1)
            warning = w[0]
            self.assertTrue(issubclass(warning.category, reader.ConfigWarning))
            self.assertIn('field', str(warning.message))

    def test_unknown_section_warning(self):
        prepare_config_file('warnings')
        config_structure = {}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            reader.IniConfig(CONFIG_FILENAME, config_structure)
            self.assertEqual(len(w), 1)
            warning = w[0]
            self.assertTrue(issubclass(warning.category, reader.ConfigWarning))
            self.assertIn('section', str(warning.message))


if __name__ == '__main__':
    unittest.main()
