"""
This file defines the different plugin types that jasper supports.

Basically, a plugin has the following structure:

some-plugin/
    some-plugin.py
    some-plugin.jasperplugin
    languages/
        en_US.mo
        [...]

"""

import abc
import threading

import yapsy.IPlugin
import commandphrase


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


class ConversationPlugin(AbstractPlugin, threading.Thread):
    CATEGORY = "conversation"

    def __init__(self):
        AbstractPlugin.__init__(self)
        threading.Thread.__init__(self)
        self.daemon = True

    @abc.abstractmethod
    def say(self, phrase):
        pass

    @abc.abstractmethod
    def run(self):
        pass


class SpeechHandlerPlugin(AbstractPlugin, commandphrase.CommandPhraseMixin):
    CATEGORY = "speechhandler"

    def __init__(self):
        AbstractPlugin.__init__(self)
        commandphrase.CommandPhraseMixin.__init__(self)


class EventHandlerPlugin(AbstractPlugin):
    CATEGORY = "eventhandler"

    def __init__(self):
        super(EventHandlerPlugin, self).__init__()

    @abc.abstractmethod
    def handle(self, phrase):
        pass


class STTPlugin(AbstractPlugin):
    CATEGORY = "stt"

    def __init__(self):
        super(STTPlugin, self).__init__()

    @abc.abstractmethod
    def transcribe(self, audio_data, language="en_US"):
        """
        Transcribes audio_data and returns text.
        """
        pass

    @abc.abstractmethod
    def get_languages():
        """
        Returns a list of available languages.
        """
        pass


class TTSPlugin(AbstractPlugin):
    CATEGORY = "tts"

    def __init__(self):
        super(TTSPlugin, self).__init__()

    @abc.abstractmethod
    def synthesize(self, phrase, language="en_US"):
        """
        Synthesizes phrase and returns wave data.
        """
        pass

    @abc.abstractmethod
    def get_languages():
        """
        Returns a list of available languages.
        """
        pass
