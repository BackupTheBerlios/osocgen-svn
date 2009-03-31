#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Defines and parses UNIX-style flags to modify command arguments.
"""

if __name__ == "__main__":
    import os.path as path
    import sys

    dirname, base = path.split(path.dirname(path.realpath(__file__)))
    sys.path.append(dirname)

from thirdparty.pyparsing import Word, Group, Literal, Dict, OneOrMore
from thirdparty.pyparsing import downcaseTokens, oneOf
from thirdparty.pyparsing import alphas, alphanums, quotedString, removeQuotes
from thirdparty.pyparsing import ParseException

from utils import to_boolean

def convertFlags(org_string, location, tokens):
    # pylint: disable-msg=W0613
    return [tokens[0], True]

class ArgsError(Exception):
    """Exception raised when errors detected during arguments parsing.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message
        
class ArgsSet(object):
    _key = Word(alphas, alphanums + "_").setParseAction(downcaseTokens)
    _long_flags = Group(Literal("--").suppress() + Word(alphas, alphanums + "_").setParseAction(convertFlags))
    #_short_flags = Group(Literal("-").suppress() + Word(alphas, max=1).setParseAction(convertFlags))
    _short_flags = Group(Literal("-").suppress() + Word(alphas, alphanums + "_").setParseAction(convertFlags))
    _EQ = oneOf(": =").suppress()
    _quotedstring = quotedString.setParseAction(removeQuotes)
    _token = Word(alphanums + "-./_:*+=")
    _value = _quotedstring  | _token
    _param = Group(_key + _EQ + _value)
    _term = _param | _short_flags | _long_flags

    def __init__(self, **kwargs):
        self.default_args = kwargs
        self.argsParser = Dict(OneOrMore(self._term))

    def parse(self, arg):
        """
        Finds flags; returns {flag: (values, if any)} and the remaining argument.
        """
        try:
            args = self.argsParser.parseString(arg)
        except ParseException:
            #TODO: Use error raising!!!
            #raise ArgsError("Parsing error.")
            return None

        for (key, value) in self.default_args.items():
            # If argument isn't defined, add it width default value
            if key not in args.keys():
                args[key] = value

            # Convert integer value
            if(isinstance(value, int)):
                try:
                    args[key] = int(args[key])
                except ValueError:
                    args[key] = 0
            
            # Convert booleans
            if(isinstance(value, bool)):
                args[key] = to_boolean(args[key])
               
        return args

if __name__ == "__main__":
    args = ArgsSet(name=None, scope="all", order=0, istop=0)
    args.parse("name=toto --zob")
