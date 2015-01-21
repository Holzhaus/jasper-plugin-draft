import SimpleXMLRPCServer
import collections
import logging
import core.plugintypes


class XMLRPCConversation(core.plugintypes.ConversationPlugin):
    def configure(self):
        self.register_option('host', default_value="localhost")
        self.register_option('port', default_value=8765)

    def activate(self):
        self._host = self.get_option('host')
        self._port = int(self.get_option('port'))
        self._server = SimpleXMLRPCServer.SimpleXMLRPCServer(
            (self._host, self._port), requestHandler=LogRequestHandler,
            allow_none=True)
        self._server.register_introspection_functions()
        self._server.register_function(self.delegate_input, 'handle')
        self._server.register_function(self.get_answers, 'get_answers')
        self._server.register_function(self.get_command_phrases,
                                       'get_command_phrases')
        print(self.get_command_phrases())
        self._answers = collections.deque([], 10)

    def deactivate(self):
        del self._host
        del self._port
        del self._server
        del self._answers

    def say(self, phrase):
        self._answers.appendleft(phrase)

    def get_answers(self):
        answers = list(self._answers)
        self._answers.clear()
        return answers

    def run(self):
        print("XMLRPC server now listening on http://%s:%s"
              % (self._host, self._port))
        self._server.serve_forever()


class LogRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    def log_request(self, code='-', size='-'):
        logging.getLogger(__name__).info('"%s" %s %s', self.requestline,
                                         str(code), str(size))
