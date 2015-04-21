from .base import AbstractPlugin
from ..commandphrase import CommandPhraseMixin


class SpeechHandlerPlugin(AbstractPlugin, CommandPhraseMixin):
    CATEGORY = "speechhandler"

    def __init__(self):
        AbstractPlugin.__init__(self)
        CommandPhraseMixin.__init__(self)
