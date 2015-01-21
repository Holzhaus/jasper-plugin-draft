#!/usr/bin/env python2
# -*- coding: utf-8-*-
import logging
import time
from core import pluginmanager, configmanager

logging.basicConfig(level=logging.INFO)


class App(object):
    def __init__(self):
        self.config = configmanager.ConfigManager()
        self.plugins = pluginmanager.PluginManager(self.config, ['plugins'])

        print("********************")
        print("* Detected Plugins *")
        print("********************")
        for plugin in self.plugins.get_all_plugins():
            print("%s %r" % (plugin.name, plugin.categories))
            print("  (%s)" % plugin.description)

        print("")
        print("************************")
        print("* Skeleton config file *")
        print("************************")
        import tempfile
        with tempfile.TemporaryFile() as f:
            self.config.write_to_fp(f)
            f.seek(0)
            print(f.read())

        for plugin in self.plugins.get_all_plugins():
            plugin.plugin_object.activate()

        conv_plugins = self.plugins.get_plugins_of_category('conversation')
        if len(conv_plugins) > 0:
            self.conv = conv_plugins[0].plugin_object
        else:
            print("No conversation plugins found")
            self.conv = None

    def run(self):
        print("******************")
        print("* Testing things *")
        print("******************")
        if not self.conv:
            print("NOP")
            return
        # test things
        for phrase in ["switch kitchen lights on",
                       "switch bathroom lights off",
                       "foo bar"]:
            print("YOU: %s" % phrase)
            self.conv.delegate_input(phrase)
        self.conv.start()
        while True:
            time.sleep(1)

if __name__ == "__main__":
    app = App()
    app.run()
