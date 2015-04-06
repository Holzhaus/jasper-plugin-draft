# -*- coding: utf-8-*-
import logging
import ConfigParser
import slugify


class UnknownOptionError(Exception):
    pass


class ConfigManager(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._reg = {}
        self._values = ConfigParser.RawConfigParser()

    def clear(self):
        for section in self._values.sections():
            self._values.remove_section(section)

    def load_values(self, filename):
        try:
            self._values.read(filename)
        except ConfigParser.Error:
            self._logger.warning("Unable to parse file '%s'", filename)
            return
        for section in self._values.sections():
            if section != slugify.slugify(section):
                self._logger.warning("Section name '%s' in '%s' is invalid " +
                                     "and will be ignored", section, filename)
                continue
            elif section not in self._reg:
                self._logger.warning("Section %s in '%s' is not registered " +
                                     "and will be ignored", section, filename)
                continue
            for option in self._values[section].options():
                if option != slugify.slugify(option):
                    self._logger.warning("Option name '%s/%s' in '%s' is " +
                                         "invalid and will be ignored",
                                         section, option, filename)
                elif option not in self._reg[section]:
                    self._logger.warning("Option %s/%s in '%s' is not " +
                                         "registered and will be ignored",
                                         section, option, filename)

    def register_option(self, section, name, default_value='',
                        is_boolean=False, desc=''):
        section_s, name_s = slugify.slugify(section), slugify.slugify(name)
        if (section_s, name_s) != (section, name):
            raise ValueError("Invalid option name '%s/%s', try '%s/%s"
                             % (section, name, section_s, name_s))
        if section not in self._reg:
            self._reg[section] = {}
        if name in self._reg[section]:
            self._logger.warning('Option %s/%s is already registered, ' +
                                 'overwriting previous settings', section,
                                 name)
        self._reg[section][name] = (default_value, is_boolean, desc)

    def get(self, section, name):
        try:
            default_value, is_boolean, desc = self._reg[section][name]
        except KeyError:
            raise UnknownOptionError("Option '%s/%s' not registered"
                                     % (section, name))
        if self._values.has_option(section, name):
            if is_boolean:
                value = self._values.getboolean(section, name)
            else:
                value = self._values.get(section, name)
        else:
            self._logger.debug("Option %s/%s not set, using default '%s'",
                               section, name, default_value)
            value = default_value
        return value

    def write_to_fp(self, f, write_comments=True, maxlen=80):
        sections = []
        # Assure that 'core' is the first section
        if 'core' in self._reg:
            sections.append('core')
        # now all other non-plugin sections
        sections.extend(sorted([section for section in self._reg.keys()
                                if not section.startswith("plugin-") and
                                not section == 'core']))
        # Finally, the plugin sections
        sections.extend(sorted([section for section in self._reg.keys()
                                if section.startswith("plugin-")]))
        # We got our section order, now write them to the fp
        for section in sections:
            # Write section headers
            f.write('[%s]\n' % section)
            for option in sorted(self._reg[section].keys()):
                default_value, is_boolean, desc = self._reg[section][option]

                # Write comments
                if write_comments and desc:
                    splitpoint = 0
                    if (maxlen-2) > 0:
                        while len(desc[splitpoint:]) > (maxlen-2):
                            splitpoint = desc.rfind(' ', beg=splitpoint,
                                                    end=splitpoint+(maxlen-2))
                            if splitpoint > 0:
                                f.write('# %s\n' % desc[:splitpoint])
                    f.write('# %s\n' % desc[splitpoint:])

                # Write option/value pairs
                f.write('#%s = %s\n' % (option, str(default_value)))
            f.write('\n')
