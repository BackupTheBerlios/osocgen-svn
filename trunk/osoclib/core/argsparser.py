#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Defines and parses UNIX-style flags to modify command arguments.
"""

if __name__ == "__main__":
    import os.path as dir
    import sys

    dirname, base = dir.split(dir.dirname(dir.realpath(__file__)))
    sys.path.append(dirname)

from thirdparty.pyparsing import *

def convertFlags(org_string, location, tokens):
    return [tokens[0], True]

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
        self.args = kwargs
        self.argsParser = Dict(OneOrMore(self._param))
        self.argsParser = Dict(OneOrMore(self._term))

    def parse(self, arg):
        """
        Finds flags; returns {flag: (values, if any)} and the remaining argument.
        """
        try:
            args = self.argsParser.parseString(arg)

            for (key,value) in self.args.items():
                # If argument isn't defined, add it width default value
                if key not in args.keys():
                    args[key] = value

                # Convert integer value
                if(isinstance(value, int)):
                   args[key] = int(args[key])
                
                # Convert booleans
                if(isinstance(value, bool)):
                   args[key] = bool(args[key])
                   
            return args
        except:
            return None

if __name__ == "__main__":
    args = ArgsSet(name=None, scope="all", order=0, istop=0)
    args.parse("name=toto --zob")
