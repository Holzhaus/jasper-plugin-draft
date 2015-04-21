import abc
from .base import AbstractPlugin


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
