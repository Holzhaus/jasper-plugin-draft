import logging
import imp
import urlparse
import slugify
from distutils.spawn import find_executable
from yapsy.FilteredPluginManager import FilteredPluginManager


# FIXME: These Two values should not be hardcoded
CURRENT_JASPERVERSION = (2, 0, 0)
NETWORK_AVAILABLE = True
LANGUAGE = "en_US"


class PluginCheckDecorator(FilteredPluginManager):
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
