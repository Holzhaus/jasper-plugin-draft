import SimpleXMLRPCServer
import collections
import plugintypes


class XMLRPCConversation(plugintypes.ConversationPlugin):
    def __init__(self, *args, **kwargs):
        plugintypes.ConversationPlugin.__init__(self, *args, **kwargs)
        self._server = SimpleXMLRPCServer.SimpleXMLRPCServer(
            ("localhost", 8765), allow_none=True)
        self._server.register_introspection_functions()
        self._server.register_function(self.delegate_input, 'handle')
        self._server.register_function(self.get_answers, 'get_answers')
        self._server.register_function(self.get_command_phrases,
                                       'get_command_phrases')
        print(self.get_command_phrases())
        self._answers = collections.deque([], 10)

    def say(self, phrase):
        self._answers.appendleft(phrase)

    def get_answers(self):
        answers = list(self._answers)
        self._answers.clear()
        return answers

    def run(self):
        print("XMLRPC server now listening on http://localhost:8765")
        self._server.serve_forever()
