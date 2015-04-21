import abc
import threading
from .base import AbstractPlugin


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
