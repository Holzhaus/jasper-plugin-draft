import gettext
import yapsy.PluginManagerDecorator


class PluginGettextDecorator(
        yapsy.PluginManagerDecorator.PluginManagerDecorator):
    def __init__(self, configmanager, *args, **kwargs):
        self._configmanager = configmanager
        super(self.__class__, self).__init__(*args, **kwargs)

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
