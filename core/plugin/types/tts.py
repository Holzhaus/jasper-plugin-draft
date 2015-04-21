import abc
from .base import AbstractPlugin


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
