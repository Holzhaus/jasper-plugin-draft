#!/usr/bin/env python2
import re
import string
import itertools


class CommandPhrase(object):
    def __init__(self, base_phrase, handler_func, variables={}):
        self._base_phrase = base_phrase
        self._handler_func = handler_func
        self._variables = variables

        # Get placeholders
        # e.g ['action', 'tool'] for 'do {action} with {tool}'
        self._placeholders = [x[1] for x in
                              string.Formatter().parse(self._base_phrase)
                              if x[1] is not None]

        # Generate regex pattern from base_phrase
        # FIXME: Sample implementation, I think that this can be improved
        placeholder_values = {}
        for placeholder in self._placeholders:
            placeholder_values[placeholder] = '(?P<{}>.+)'.format(placeholder)
        regex_phrase = "^{}$".format(
            self._base_phrase.format(**placeholder_values))
        self._pattern = re.compile(regex_phrase, re.LOCALE | re.UNICODE)

    @property
    def handler_func(self):
        """
        The handler_func associated with this CommandPhrase.
        """
        return self._handler_func

    @property
    def combinations(self):
        """
        Output all possible phrases (i.e. word combinations) of this
        CommandPhrase. Needed for vocabulary compilation.
        """
        # FIXME: Sample implementation, there might be a better one
        phrases = []
        factors = [self._variables[p] for p in self._placeholders]
        combinations = itertools.product(*factors)
        for combination in combinations:
            replacement_values = dict(zip(self._placeholders, combination))
            phrases.append(self._base_phrase.format(**replacement_values))
        return phrases

    @property
    def pattern(self):
        """
        The regex pattern of this CommandPhrase.
        """
        return self._pattern

    def match(self, phrase):
        """
        Looks for a match of this CommandPhrase in phrase.
        """
        matchobj = self.pattern.match(phrase)
        if matchobj:
            return matchobj
        return None


class CommandPhraseMixin(object):
    def __init__(self):
        self._commands = []

    def register_command(self, cmdstring, function, **variables):
        cmd = CommandPhrase(cmdstring, function, variables)
        self._commands.append(cmd)

    def get_command_phrases(self):
        combinations = [c.combinations for c in self._commands]
        return list(itertools.chain.from_iterable(combinations))

    def get_handler(self, phrase):
        for cmd in self._commands:
            matchobj = cmd.match(phrase)
            if matchobj:
                return (cmd.handler_func, matchobj.groupdict())
