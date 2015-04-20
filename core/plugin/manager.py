import operator
import itertools
import logging
import yapsy
import yapsy.PluginFileLocator
import yapsy.PluginManager
from . import types
from . import info
from . import decorators
from . import analyzer


class PluginManager(object):
    PLUGIN_CATS = {types.ConversationPlugin.CATEGORY:
                   types.ConversationPlugin,
                   types.SpeechHandlerPlugin.CATEGORY:
                   types.SpeechHandlerPlugin,
                   types.EventHandlerPlugin.CATEGORY:
                   types.EventHandlerPlugin,
                   types.TTSPlugin.CATEGORY:
                   types.TTSPlugin,
                   types.STTPlugin.CATEGORY:
                   types.STTPlugin}

    def __init__(self, config, directories_list):
        locator = yapsy.PluginFileLocator.PluginFileLocator(
            analyzers=[analyzer.FileAnalyzer('info-ext', 'jasperplugin')])
        locator.setPluginInfoClass(info.PluginInfo)
        pm = yapsy.PluginManager.PluginManager(
            categories_filter=self.PLUGIN_CATS,
            directories_list=directories_list,
            plugin_locator=locator)
        pm = decorators.PluginCheckDecorator(config, pm)
        pm = decorators.PluginConfigDecorator(config, pm)
        pm = decorators.PluginGettextDecorator(config, pm)
        self._pm = pm
        self._pm.collectPlugins()
        for plugin_info in self.get_plugins_of_category(
                types.ConversationPlugin.CATEGORY):
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
                         types.SpeechHandlerPlugin.CATEGORY)]
                    if handler is not None]

    def get_command_phrases(self):
        phrases = [plugin.plugin_object.get_command_phrases()
                   for plugin in self.get_plugins_of_category(
                       types.SpeechHandlerPlugin.CATEGORY)]
        return sorted(list(set(itertools.chain.from_iterable(phrases))))
