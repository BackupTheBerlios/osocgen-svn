#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     vhdl.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2007/04/03
# Licence:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = \
"""This programme will be able to generate intercon module for an Ochestra system.
"""
__version__ = "$Id$"
__versionTime__ = "22/03/2007"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPL"
__copyright__ = "Copyright 2008 Fabrice MOUSSET"

import os
import re
import sys
import string
from optparse import OptionParser
from thirdparty.pyparsing import *

class Entity:
    """  VHDL entity parser class.

    entity_declaration ::=
        ENTITY <identifier> IS
        [ GENERIC ( <generic_list> ) ; ]
        [ PORT ( <port_list> ) ; ]
        END [ ENTITY] [ <identifier> ] ;

    generic_list  ::=
        <generic_declaration> {; <generic_declaration> }

    generic_declaration ::=
        <identifier> : <mode> <subtype_indication> [ := <static_expression> ]

    port_list ::=
        <port_declaration> {; <port_declaration> }

    port_declaration ::=
        <identifier> : [ mode ] <subtype_indication>

    mode ::=
        IN | OUT | INOUT | BUFFER | LINKAGE

    subtype_indication ::=
        <identifier> [ ( <expression> TO | DOWNTO <expression> ) ]
    """

    # VHDL Entity cleaners. Used in parsing, but doesn't clutter up results
    __SEMI = Literal(";").suppress()
    __LPAR = Literal("(").suppress()
    __RPAR = Literal(")").suppress()
    __COLON = Literal(":").suppress()
    __EQUAL = Literal(":=").suppress()

    # VHDL Entity data extractors.
    __identifier = Word(alphas, alphanums + "_")
    __integer = Word(nums).setParseAction(lambda t:int(t[0]))
    __hexaValue = Combine('X"' + Word(hexnums) + '""')
    __vectorValue = Combine('"' + Word("01X") + '"')
    __bitValue = Combine("'" + Word("01X", max=1) + "'")
    __arithOp = Word("+-*/", max=1)

    __comment = Literal("--").suppress() + Optional( restOfLine )

    __entityIdent = __identifier.setResultsName("entityId")
    __mode = oneOf("IN OUT INOUT BUFFER LINKAGE", caseless=True)
    __expression = Combine((__integer | __identifier) + Optional(__arithOp + (__integer | __identifier)))
    __staticExpression = __integer | __identifier | __hexaValue | __vectorValue | __bitValue
    __subtypeIndication = Group(__identifier + Optional(__LPAR + __expression + oneOf("TO DOWNTO", caseless=True) + __expression + __RPAR))
    __portDecl = Group(__identifier + __COLON + __mode + __subtypeIndication)
    __genericDecl = Group(__identifier + __COLON + __subtypeIndication + Optional(__EQUAL + __staticExpression))

    # VHDL Entity decoder
    __entityDecl = ( CaselessLiteral("ENTITY").suppress() + __entityIdent + CaselessLiteral("IS").suppress() +
        Optional(CaselessLiteral("GENERIC").suppress() + __LPAR + delimitedList(__genericDecl, delim=";").setResultsName("generic") + __RPAR + __SEMI ) +
        Optional(CaselessLiteral("PORT").suppress() + __LPAR + delimitedList(__portDecl, delim=";").setResultsName("port") + __RPAR + __SEMI) +
        CaselessLiteral("END").suppress() + Optional(CaselessLiteral("ENTITY").suppress()) + Optional(matchPreviousLiteral(__entityIdent).suppress()) + __SEMI ).ignore(__comment)

    def __init__(self, filename=None):
        """VHDL Entity extract initialisation."""
        self.filename = filename
        self._entity = None

        def extractEntity(data, line):
            """ VHDL Line parser.

            This function extract VHDL Entity declaration and remove all
            comments lines from it.
            """
            if(string.find(data, "END ENTITY") < 0 and len(line)  > 0):
                if(len(data) == 0 and string.find(line, "ENTITY") < 0):
                    return ""
                i = string.find(line, '--')
                if(i < 0):
                    return data + line + " "
                if(i > 0):
                    return data + line[:i].rstrip() + " "
            return data

        fd = filename
        if isinstance(filename, basestring):
            if(os.path.exists(filename)):
                fd = file(filename, 'r')

        if fd:
            data = ""
            for line in fd:
                data = extractEntity(data, string.upper(line.rstrip().lstrip()))
            fd.close()
            self._entity = self.__entityDecl.parseString(data)

    def __combineType(self, arg):
        """  Generaty signal type string"""
        if(len(arg) > 1):
            return arg[0] + "(" + " ".join(arg[1:]) + ")"
        return arg[0]

    def __str__(self, as_component=False):
        """  Generate entity or component declaration string"""

        if(self._entity == None):
            return "";

        if(as_component):
            data = "COMPONENT "
        else:
            data = "ENTITY "
        data += self._entity.entityId + " IS\n"

        # Add Generics declaration
        if(len(self._entity.generic) > 0):
            data += "  GENERIC (\n"
            count = 0
            for generic in self._entity.generic:
                if(count > 0):
                    data += ";\n"
                data += "    " + generic[0] + " : " + self.__combineType(generic[1])
                if(len(generic) > 2):
                    data += " := " + str(generic[2])
                count += 1
            data += "\n  );\n"

        # Add Ports declaration
        if(len(self._entity.port) > 0):
            data += "  PORT (\n"
            count = 0
            for port in self._entity.port:
                if(count > 0):
                    data += ";\n"
                data += "    " + port[0] + " : " + port[1] + " " + self.__combineType(port[2])
                count += 1
            data += "\n  );\n"

        if(as_component):
            data += "END COMPONENT;"
        else:
            data += "END ENTITY;"
        return data

    def toInstance(self, properties):
        """ Create a component instance. """

        # Creating the instance name
        instance = "  "
        if(properties.name != None):
            instance += properties.name + " : "
        instance += self._entity.entityId + "\n"

        # Adding generics values if they are defined
        if(len(self._entity.generic) > 0):
            count = 0
            data += "    GENERIC MAP(\n"
            for generic in self._entity.generic:
                if(count > 0):
                    data += ",\n"

                data += "      " + generic[0] + " => "
                # If no value passed for this generic, then we use the default one
                if(properties.generics.has_key(generic[0])):
                    data += properties.generics[generic[0]]
                else:
                    data += generic[2]
                count += 1
            data += "\n  )\n"

        # Adding ports values if they are defined
        if(len(self._entity.port) > 0):
            count = 0
            data += "    PORT MAP(\n"
            for port in self._entity.port:
                if(count > 0):
                    data += ",\n"

                data += "    " + port[0] + " => "
                # If no value passed, port is not used --> OPEN
                if(properties.ports.has_key(port[0])):
                    data += properties.ports[port[0]]
                else:
                    data += "OPEN"
                count += 1
            data += "\n  );\n"

        return;

    generics  = property(lambda self: self._entity.generic)
    ports     = property(lambda self: self._entity.port)
    def getGenerics(self):
        """
        Returns all generic parameters names.
        """
        generics = []
        if(self._entity != None):
            for generic in self._entity.generic:
                generics.append(generic[0])
        return generics

    def getGenericType(self, name):
        if(self._entity != None):
            for generic in self._entity.generic:
                if(generic[0] == name):
                    return generic[1]
        return None

    def getGenericValue(self, name):
        # FIXME: Devra être testé par la suite
        if(self._entity != None):
            for generic in self._entity.generic:
                if(generic[0] == name):
                    if(len(generic) > 2):
                        return generic[2]
                    else:
                        return None
        return None

    def getPorts(self):
        ports = []
        if(self._entity != None):
            for port in self._entity.port:
                ports.append(port[0])
        return ports

class Instance:
    """VHDL entity instance class.

    This class make the link between an ENTITY declaration and the parameters
    for a instance of this ENTITY to build a new IP.
    """

    def __init__(self, parent, name=None):
        self._parent = parent
        self._entity = parent._entity
        self.name = name
        self.ports = {}
        for port in parent._entity.port:
            self.ports[port[0]] = None

def main():
    """
    Main function, deals with arguments and launch program
    """
    entity = Entity(filename='imx_wrapper.vhd')
    print entity
    print "Les generics :"
    print entity.getGenerics()
    entity = Entity(filename='irq_mngr.vhd')
    print entity
    print entity.getGenerics()


if __name__ == '__main__':
    main()
