import yapsy.PluginFileLocator


class FileAnalyzer(yapsy.PluginFileLocator.PluginFileAnalyzerWithInfoFile):
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
