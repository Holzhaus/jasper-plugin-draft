import sys
import logging
import ConfigParser
import slugify
import yapsy
import yapsy.PluginFileLocator


class FileAnalyzer(yapsy.PluginFileLocator.PluginFileAnalyzerWithInfoFile):
    def __init__(self, *args, **kwargs):
        super(FileAnalyzer, self).__init__(*args, **kwargs)
        self._logger = logging.getLogger(__name__)

    def getPluginNameAndModuleFromStream(self, infoFileObject,
                                         candidate_infofile=None):
        # parse the information buffer to get info about the plugin
        config_parser = ConfigParser.ConfigParser()
        try:
            if sys.version_info < (3, 0):
                config_parser.readfp(infoFileObject)
            else:
                config_parser.read_file(infoFileObject)
        except Exception as e:
            self._logger.debug("Could not parse the plugin file '%s' " +
                               "(exception raised was '%s')",
                               candidate_infofile, e)
            return (None, None, None)
        # check if the basic info is available
        if not config_parser.has_section("Core"):
            self._logger.debug("Plugin info file has no 'Core' section (in " +
                               "'%s')", candidate_infofile)
            return (None, None, None)
        if (not config_parser.has_option("Core", "Name") or
                not config_parser.has_option("Core", "Slug")):
            self._logger.debug("Plugin info file has no 'Name' or 'Slug' " +
                               "section (in '%s')" % candidate_infofile)
            return (None, None, None)
        # check that the given name is valid
        name = config_parser.get("Core", "Name").strip()
        if yapsy.PLUGIN_NAME_FORBIDEN_STRING in name:
            self._logger.debug("Plugin name contains forbidden character: %s" +
                               " (in '%s')", yapsy.PLUGIN_NAME_FORBIDEN_STRING,
                               candidate_infofile)
            return (None, None, None)
        # check that the given slug is valid
        slug = config_parser.get("Core", "Slug").strip()
        if len(slug) < 5:
            self._logger.warning("Plugin slug too short (< 5 chars): '%s' " +
                                 "(in '%s')", slug, candidate_infofile)
            return (None, None, None)
        valid_slug = slugify.slugify(slug)
        if slug != valid_slug:
            self._logger.warning("Plugin slug invalid: '%s' != '%s' (in '%s')",
                                 slug, valid_slug, candidate_infofile)
            return (None, None, None)
        return (name, "plugin", config_parser)
