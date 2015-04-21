"""
This file defines the different plugin types that jasper supports.

Basically, a plugin has the following structure:

some-plugin/
    plugin.py
    plugin.info
    languages/
        en_US.mo
        [...]

"""

from .conversation import ConversationPlugin
from .speechhandler import SpeechHandlerPlugin
from .stt import STTPlugin
from .tts import TTSPlugin

__all__ = ['ConversationPlugin', 'SpeechHandlerPlugin', 'STTPlugin',
           'TTSPlugin']
