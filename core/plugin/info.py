import os
import ConfigParser
import logging
import yapsy.PluginInfo


class PluginInfo(yapsy.PluginInfo.PluginInfo):

    def __init__(self, plugin_name, plugin_path):
        super(self.__class__, self).__init__(plugin_name, plugin_path)
        self._logger = logging.getLogger(__name__)

    @property
    def slug(self):
        return self.details.get('Core', 'Slug')

    @property
    def license(self):
        if self.details.has_option('Documentation', 'License'):
            return self.details.get('Documentation', 'License')

    @property
    def priority(self):
        try:
            value = int(self.details.get('Documentation', 'Priority'))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = 0
        return value

    @property
    def depends_jasperversion(self):
        try:
            versionstr = self.details.get('Dependencies', 'JasperVersion')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = (2, 0, 0)
        else:
            value = tuple(int(n) for n in versionstr.split('.'))
        return value

    @property
    def depends_network(self):
        try:
            value = self.details.getboolean('Dependencies', 'Network')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = False
        return value

    @property
    def depends_executables(self):
        try:
            csvlst = self.details.get('Dependencies', 'Binaries')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = []
        else:
            value = [item.strip() for item in csvlst.split(',')]
        return value

    @property
    def depends_modules(self):
        try:
            csvlst = self.details.get('Dependencies', 'Modules')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = []
        else:
            value = [item.strip() for item in csvlst.split(',')]
        return value

    @property
    def depends_plugins(self):
        try:
            csvlst = self.details.get('Dependencies', 'Plugins')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            value = []
        else:
            value = [item.strip() for item in csvlst.split(',')]
        return value

    @property
    def supported_languages(self):
        path = os.path.join(os.path.dirname(self.path), "languages")
        langs = set()
        if os.path.exists(path):
            langs = set(os.path.splitext(os.path.basename(filename))[0]
                        for filename in os.listdir(path)
                        if os.path.splitext(filename)[1] == "%smo" % os.extsep)
        # Return en_US if plugin is not translated
        return set(['en_US']) if not langs else langs

    def get_translations_path(self, language):
        os.path.dirname(self.path)
        if language is not None:
            language_file = os.path.join(os.path.dirname(self.path),
                                         "languages",
                                         os.extsep.join([language, 'mo']))
            if os.access(language_file, os.R_OK):
                return language_file
        return None
