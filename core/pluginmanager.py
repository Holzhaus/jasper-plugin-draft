import logging
import imp
import operator
import urlparse
import slugify
from distutils.spawn import find_executable
import ConfigParser
import itertools


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
    def is_available(self):
        # Check Jasperversion
        if self.depends_jasperversion > CURRENT_JASPERVERSION:
            needed_version_str = '.'.join(
                str(n) for n in self.depends_jasperversion)
            current_version_str = '.'.join(
                str(n) for n in CURRENT_JASPERVERSION)
            self._logger.info("Plugin '%s' rejected: Jasper is outdated " +
                              "(%s > %s)", self.name, needed_version_str,
                              current_version_str)
            return False

        # Check Network
        if self.depends_network and not NETWORK_AVAILABLE:
            self._logger.info("Plugin '%s' rejected: Needs network connection",
                              self.name)
            return False

        # Check executables
        for executable_name in self.depends_executables:
            if not find_executable(executable_name):
                self._logger.info("Plugin '%s' rejected: Needs executable " +
                                  "'%s'", self.name, executable_name)
                return False

        # Check modules
        for module_name in self.depends_modules:
            try:
                imp.find_module(module_name)
            except ImportError:
                self._logger.info("Plugin '%s' rejected: Needs module '%s'",
                                  self.name, module_name)
                return False

        # Everything worked, this module is available
        return True


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
        self._pm = _ConfPluginManager(config, _FilterPluginManager(pm))
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

"""
class _I18nPluginManager(yapsy.PluginManagerDecorator.PluginManagerDecorator):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def __add_translations(self, plugin_info):
        localedir = os.path.join(os.path.dirname(plugin_info.path), 'locale')

        plugin_info.gettext_object = gettext.translation(plugin_info.slug,
                                                         localedir,
                                                         fallback=True
                                                         languages=)
        plugin_mod = sys.modules[plugin_info.plugin_object.__module__]
        plugin_mod._ = plugin_info.gettext_object.ugettext

    def loadPlugins(self, *args, **kwargs):
        self._component.loadPlugins(*args, **kwargs)
        for plugin_info in self._component.getAllPlugins():
            self.__add_translations(plugin_info)"""


class _ConfPluginManager(yapsy.PluginManagerDecorator.PluginManagerDecorator):
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


class _FilterPluginManager(yapsy.FilteredPluginManager.FilteredPluginManager):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)

    def isPluginOk(self, info):
        slug = slugify.slugify(info.slug)
        if len(slug) == 0:
            self._logger.warning("Rejecting plugin '%s' (Core/Slug not set)",
                                 info.name)
            return False
        elif len(slug) < 5:
            self._logger.warning("Rejecting plugin '%s' (Core/Slug too short)",
                                 info.name)
            return False
        if info.slug != slug:
            self._logger.warning("Rejecting plugin '%s' (Core/Slug '%s' " +
                                 "invalid, try '%s')", info.name, info.slug,
                                 slug)
            return False

        if not info.author or info.author == "Unknown":
            self._logger.warning("Rejecting plugin '%s' (Documentation/" +
                                 "Author is missing)", info.name)
            return False

        if not info.description:
            self._logger.warning("Rejecting plugin '%s' (Documentation/" +
                                 "Description is missing)", info.name)
            return False

        try:
            info.version
        except ValueError:
            self._logger.warning("Rejecting plugin '%s' (Documentation/" +
                                 "Version is invalid)", info.name)
            return False

        if info.website and info.website != "None":
            url = urlparse.urlparse(info.website)
            if not url.netloc or url.scheme not in ('http', 'https'):
                self._logger.warning("Rejecting plugin '%s' (Documentation/" +
                                     "Website is not a valid URL)", info.name)
                return False

        # Check license
        if not info.license:
            self._logger.warning("Rejecting plugin '%s' (Documentation/" +
                                 "License not set)", info.name)
            return False

        return info.is_available
