import abc
import yapsy.IPlugin


class GettextPluginMixin(object):
    """
    These is just a dummy plugin mixin. These methods are
    overwritten at runtime by the GettextPluginDecorator and are only
    implemented here in case we want to dectivate the decorator for
    some reason (and to quiet our source code linters).
    """
    def gettext(self, message):
        return message

    def ngettext(self, singular, plural, n):
        return singular if n == 1 else plural


class ConfigPluginMixin(object):
    """
    These is just a dummy plugin mixin. These methods are
    overwritten at runtime by the ConfigPluginDecorator and are only
    implemented here in case we want to dectivate the decorator for
    some reason (and to quiet our source code linters).
    """
    def register_option(*args, **kwargs):
        pass

    def get_option(*args, **kwargs):
        pass


class AbstractPlugin(yapsy.IPlugin.IPlugin, GettextPluginMixin,
                     ConfigPluginMixin):
    """
    The base class for all plugins.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        yapsy.IPlugin.IPlugin.__init__(self)

    def configure(self):
        pass
