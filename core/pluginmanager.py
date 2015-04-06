import logging
import imp
import operator
import urlparse
import slugify
from distutils.spawn import find_executable
import ConfigParser
import itertools
import os
import gettext


import plugintypes
import yapsy
import yapsy.PluginFileLocator
import yapsy.PluginInfo
import yapsy.PluginManager
import yapsy.PluginManagerDecorator
import yapsy.FilteredPluginManager

# FIXME: These Two values should not be hardcoded
CURRENT_JASPERVERSION = (2, 0, 0)
NETWORK_AVAILABLE = True
LANGUAGE = "en_US"


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


class PluginManager(object):
    PLUGIN_CATS = {plugintypes.ConversationPlugin.CATEGORY:
                   plugintypes.ConversationPlugin,
                   plugintypes.SpeechHandlerPlugin.CATEGORY:
                   plugintypes.SpeechHandlerPlugin,
                   plugintypes.EventHandlerPlugin.CATEGORY:
                   plugintypes.EventHandlerPlugin,
                   plugintypes.TTSPlugin.CATEGORY:
                   plugintypes.TTSPlugin,
                   plugintypes.STTPlugin.CATEGORY:
                   plugintypes.STTPlugin}

    def __init__(self, config, directories_list):
        locator = yapsy.PluginFileLocator.PluginFileLocator(
            analyzers=[_FileAnalyzer('info-ext', 'jasperplugin')])
        locator.setPluginInfoClass(PluginInfo)
        pm = yapsy.PluginManager.PluginManager(
            categories_filter=self.PLUGIN_CATS,
            directories_list=directories_list,
            plugin_locator=locator)
        self._pm = PluginGettextDecorator(
          config, PluginConfigDecorator(config, PluginChecker(config, pm)))
        self._pm.collectPlugins()
        for plugin_info in self.get_plugins_of_category(
                plugintypes.ConversationPlugin.CATEGORY):
            self.__add_conversation_methods(plugin_info.plugin_object)

    def __add_conversation_methods(self, plugin_object):
        PM = self

        def plugin_delegate_input(phrase):
            handler = PM.find_handler(phrase)
            if handler:
                handler_func, variables = handler
                handler_func(plugin_object, **variables)
            else:
                logging.getLogger(__name__).warning(
                    "No plugin can handle '%s'", phrase)

        def plugin_get_command_phrases():
            return PM.get_command_phrases()

        plugin_object.delegate_input = plugin_delegate_input
        plugin_object.get_command_phrases = plugin_get_command_phrases

    def get_plugin_by_slug(self, slug, category="Default"):
        """
        Get the plugin correspoding to a given category and slug
        """
        for item in self._pm.getPluginsOfCategory(category):
            if item.slug == slug:
                return item
        return None

    def get_plugins_of_category(self, category_name):
        available_plugins = self._pm.getPluginsOfCategory(category_name)
        # sort on secondary key
        available_plugins.sort(key=operator.attrgetter('slug'))
        # now sort on primary key, descending
        available_plugins.sort(key=operator.attrgetter('priority'),
                               reverse=True)
        return available_plugins

    def get_all_plugins(self):
        return self._pm.getAllPlugins()

    def find_handler(self, phrase):
        handlers = self.find_handlers(phrase)
        if len(handlers) > 0:
            return handlers[0]

    def find_handlers(self, phrase):
            return [handler for handler in
                    [plugin.plugin_object.get_handler(phrase)
                     for plugin in self.get_plugins_of_category(
                         plugintypes.SpeechHandlerPlugin.CATEGORY)]
                    if handler is not None]

    def get_command_phrases(self):
        phrases = [plugin.plugin_object.get_command_phrases()
                   for plugin in self.get_plugins_of_category(
                       plugintypes.SpeechHandlerPlugin.CATEGORY)]
        return sorted(list(set(itertools.chain.from_iterable(phrases))))


class _FileAnalyzer(yapsy.PluginFileLocator.PluginFileAnalyzerWithInfoFile):
    def getInfosDictFromPlugin(self, *args, **kwargs):
        try:
            return super(self.__class__, self).getInfosDictFromPlugin(
                *args, **kwargs)
        except ValueError:
            return (None, None)

    def _extractCorePluginInfo(self, *args, **kwargs):
        infos, config_parser = \
            super(self.__class__, self)._extractCorePluginInfo(*args, **kwargs)
        # check slug
        if not config_parser or not config_parser.has_option('Core', 'Slug'):
            return (None, None)
        return (infos, config_parser)


class PluginConfigDecorator(
        yapsy.PluginManagerDecorator.PluginManagerDecorator):
    def __init__(self, configmanager, *args, **kwargs):
        self._configmanager = configmanager
        super(self.__class__, self).__init__(*args, **kwargs)

    def __add_config_methods(self, plugin_slug, plugin_object):
        """
        Add two methods to the plugin objects that will make it
        possible for it to benefit from this class's api concerning
        the management of the options.
        """
        CM = self._configmanager
        SECTION = 'plugin-%s' % plugin_slug

        def plugin_register_option(name, **kwargs):
            return CM.register_option(SECTION, name, **kwargs)

        def plugin_get_option(name):
            return CM.get(SECTION, name)

        plugin_object.register_option = plugin_register_option
        plugin_object.get_option = plugin_get_option

    def loadPlugins(self, *args, **kwargs):
        self._component.loadPlugins(*args, **kwargs)
        for plugin_info in self._component.getAllPlugins():
            self.__add_config_methods(plugin_info.slug,
                                      plugin_info.plugin_object)
            plugin_info.plugin_object.configure()


class PluginGettextDecorator(
        yapsy.PluginManagerDecorator.PluginManagerDecorator):
    def __init__(self, configmanager, *args, **kwargs):
        self._configmanager = configmanager
        super(self.__class__, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)

    def get_translations(self, plugin_info, language):
        translations_path = plugin_info.get_translations_path(language)
        if translations_path is not None:
            with open(translations_path, "rb") as f:
                translations = gettext.GNUTranslations(f)
                # Check if translations file is valid
                try:
                    translations.info()
                except gettext.LookupError:
                    self._logger.warning("Plugin '%s' has an invalid " +
                                         "translations file: %s",
                                         plugin_info.name, translations_path)
                    return gettext.NullTranslations()
                else:
                    translations.add_fallback(gettext.NullTranslations())
                    return translations
        self._logger.info("Plugin '%s' is missing a translations file, " +
                          "assuming hardcoded en_US strings.",
                          plugin_info.name)
        return gettext.NullTranslations()

    def __add_gettext_methods(self, plugin_info, plugin_object):
        """
        Add two methods to the plugin objects that will make it
        possible for it to benefit from this class's api concerning
        the management of the options.
        """
        language = self._configmanager.get("core", "language")
        TRANSLATIONS = self.get_translations(plugin_info, language)

        def plugin_gettext(*args):
            return TRANSLATIONS.ugettext(*args)

        def plugin_ngettext(*args):
            return TRANSLATIONS.ungettext(*args)

        plugin_object.gettext = plugin_gettext
        plugin_object.ngettext = plugin_ngettext

    def loadPlugins(self, *args, **kwargs):
        self._component.loadPlugins(*args, **kwargs)
        for plugin_info in self._component.getAllPlugins():
            self.__add_gettext_methods(plugin_info,
                                       plugin_info.plugin_object)


class PluginChecker(yapsy.FilteredPluginManager.FilteredPluginManager):
    def __init__(self, config, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._config = config
        self._config.register_option("plugins", "check-language-support",
                                     default_value=True, is_boolean=True)
        self._config.register_option("plugins", "check-metadata",
                                     default_value=True, is_boolean=True)
        self._config.register_option("plugins", "check-network",
                                     default_value=True, is_boolean=True)
        self._logger = logging.getLogger(__name__)

    def isPluginOk(self, info):
        slug = slugify.slugify(info.slug)
        if len(slug) == 0:
            self._logger.warning("Plugin '%s' rejected: Core/Slug not set",
                                 info.name)
            return False
        elif len(slug) < 5:
            self._logger.warning("Plugin '%s' rejected: Core/Slug too short",
                                 info.name)
            return False
        if info.slug != slug:
            self._logger.warning("Plugin '%s' rejected: Core/Slug '%s' " +
                                 "invalid, try '%s'", info.name, info.slug,
                                 slug)
            return False

        # Check Jasperversion
        if info.depends_jasperversion > CURRENT_JASPERVERSION:
            needed_version_str = '.'.join(
                str(n) for n in info.depends_jasperversion)
            current_version_str = '.'.join(
                str(n) for n in CURRENT_JASPERVERSION)
            self._logger.warning("Plugin '%s' rejected: Jasper is outdated " +
                                 "(%s > %s)", self.name, needed_version_str,
                                 current_version_str)
            return False

        # Check executables
        for executable_name in info.depends_executables:
            if not find_executable(executable_name):
                self._logger.warning("Plugin '%s' rejected: Needs executable" +
                                     " '%s'", info.name, executable_name)
                return False

        # Check modules
        for module_name in info.depends_modules:
            try:
                imp.find_module(module_name)
            except ImportError:
                self._logger.warning("Plugin '%s' rejected: Needs module '%s'",
                                     info.name, module_name)
                return False

        # Check Network
        if self._config.get("plugins", "check-network") and \
                info.depends_network and not NETWORK_AVAILABLE:
            self._logger.warning("Plugin '%s' rejected: Needs network " +
                                 "connection", info.name)
            return False

        # Check if current language is supported by this plugin
        language = self._config.get("core", "language")
        language = language if language else 'en_US'
        if self._config.get("plugins", "check-language-support") and \
                language not in info.supported_languages:
            self._logger.warning("Plugin '%s' rejected: Language %s not " +
                                 "supported", info.name, language)
            return False

        # Metadata checks, these should be optional
        if self._config.get("plugins", "check-metadata"):
            if not info.author or info.author == "Unknown":
                self._logger.warning("Plugin '%s' rejected: Documentation/" +
                                     "Author is missing", info.name)
                return False

            if not info.description:
                self._logger.warning("Plugin '%s' rejected: Documentation/" +
                                     "Description is missing", info.name)
                return False

            try:
                info.version
            except ValueError:
                self._logger.warning("Plugin '%s' rejected: Documentation/" +
                                     "Version is invalid", info.name)
                return False

            if info.website and info.website != "None":
                url = urlparse.urlparse(info.website)
                if not url.netloc or url.scheme not in ('http', 'https'):
                    self._logger.warning("Plugin '%s' rejected: " +
                                         "Documentation/Website is not a " +
                                         "valid URL", info.name)
                    return False

            if not info.license:
                self._logger.warning("Plugin '%s' rejected: Documentation/" +
                                     "License not set", info.name)
                return False

        # Everything worked, this module is available
        return True