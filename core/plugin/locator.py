import os
import yapsy.PluginFileLocator
from . import analyzer
from . import info

INFO_EXT = 'info'


class PluginLocator(yapsy.PluginFileLocator.PluginFileLocator):
    def __init__(self, *args, **kwargs):
        kwargs["analyzers"] = [analyzer.FileAnalyzer('info-ext', INFO_EXT)]
        super(PluginLocator, self).__init__(*args, **kwargs)
        self.setPluginInfoClass(info.PluginInfo)

    def locatePlugins(self):
        candidates, num = super(PluginLocator, self).locatePlugins()
        real_candidates = []
        plugin_info_name = os.extsep.join(['plugin', INFO_EXT])
        for candidate in candidates:
            info_filepath, module_filepath, plugin_info = candidate
            # Check module name
            if os.path.basename(module_filepath) != 'plugin':
                continue
            # Check infofile name
            if os.path.basename(info_filepath) != plugin_info_name:
                continue
            # Ensure that plugin is inside it's own subdir
            plugin_dir = os.path.basename(os.path.dirname(module_filepath))
            if plugin_dir in self.plugins_places:
                # This plugin is not inside its own subdir
                continue
            real_candidates.append(candidate)
        return real_candidates, len(real_candidates)
