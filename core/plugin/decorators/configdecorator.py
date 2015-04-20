import yapsy.PluginManagerDecorator


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

    def __decorate_activate_method(self, plugin_name, plugin_object):
        plugin_object.register_option('enabled',
                                      default_value=True,
                                      is_boolean=True)

        ORIGINAL_METHOD = plugin_object.activate

        def plugin_activate():
            if plugin_object.get_option('enabled'):
                ORIGINAL_METHOD()
                self._logger.info("Plugin '%s' activated.",
                                  plugin_name)
            else:
                self._logger.info("Plugin '%s' disabled in configuration.",
                                  plugin_name)
        plugin_object.activate = plugin_activate

    def loadPlugins(self, *args, **kwargs):
        self._component.loadPlugins(*args, **kwargs)
        for plugin_info in self._component.getAllPlugins():
            self.__add_config_methods(plugin_info.slug,
                                      plugin_info.plugin_object)
            self.__decorate_activate_method(plugin_info.name,
                                            plugin_info.plugin_object)
            plugin_info.plugin_object.configure()
