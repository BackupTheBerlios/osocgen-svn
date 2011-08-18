#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     vhdl.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2007/04/03
# License:  GPLv3 or newer
#=============================================================================
# Revision list :
#
# Date       By        Changes
#
#=============================================================================

"""VHDL entity manipulation routines.

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
__version__ = "$Id$"
__versionTime__ = "22/03/2007"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2008 Fabrice MOUSSET"

if __name__ == "__main__":
    import os.path as path
    import sys

    dirname, base = path.split(path.dirname(path.realpath(__file__)))
    sys.path.append(dirname)

from thirdparty.pyparsing import Literal, Word, Combine, Group, CaselessLiteral 
from thirdparty.pyparsing import Optional, Forward, ZeroOrMore, StringEnd
from thirdparty.pyparsing import delimitedList, oneOf, restOfLine, SkipTo
from thirdparty.pyparsing import alphas, alphanums, matchPreviousLiteral
from thirdparty.pyparsing import nums, hexnums, downcaseTokens

from utils import combine_type

# VHDL Entity cleaners. Used in parsing, but doesn't clutter up results
SEMI = Literal(";").suppress()
LPAR = Literal("(").suppress()
RPAR = Literal(")").suppress()
COLON = Literal(":").suppress()
EQUAL = Literal(":=").suppress()

# VHDL Entity data extractors.
identifier = Word(alphas, alphanums + "_").setParseAction(downcaseTokens)
integer = Word(nums).setParseAction(lambda t:int(t[0]))
hexaValue = Combine('X"' + Word(hexnums) + '""')
vectorValue = Combine('"' + Word("01X") + '"')
bitValue = Combine("'" + Word("01X", max=1) + "'")
arithOp = Word("+-*/", max=1)
entityIdent = identifier.setResultsName("identifier")
mode = oneOf("IN OUT INOUT BUFFER LINKAGE", caseless=True)

# VHDL comments extractor.
comment = Literal("--").suppress() + Optional(restOfLine)

# Nested operation parser
expression = Forward()
parenthical = Literal("(") + Group(expression) + Literal(")") 
operand = Word(nums) | identifier  | parenthical
expression << operand + ZeroOrMore(arithOp + operand)
   
staticExpression = (integer | identifier | hexaValue | vectorValue | bitValue)

# Type information parser
subtypeIndication = Group(identifier + 
                          Optional(LPAR + Combine(expression) + 
                                   oneOf("TO DOWNTO", caseless=True) + 
                                   Combine(expression) + RPAR
                                   )
                          )

# Port declaration parser
portDecl = Group(identifier + COLON + mode + subtypeIndication)
portList = delimitedList(portDecl, delim=";").setResultsName("ports")

# Generic declaration parser
genericDecl = Group(identifier + COLON + subtypeIndication + 
                    Optional(EQUAL + staticExpression)
                    )
genericList = delimitedList(genericDecl, delim=";").setResultsName("generics")

# VHDL Entity declaration decoder
entityHeader = (CaselessLiteral("ENTITY").suppress() + entityIdent + 
    CaselessLiteral("IS").suppress()
    )

# Full VHDL Entity decoder
entityDecl = (SkipTo(entityHeader) + entityHeader +
              Optional(CaselessLiteral("GENERIC").suppress() + LPAR + 
                       genericList + RPAR + SEMI
                       ) +
              Optional(CaselessLiteral("PORT").suppress() + LPAR + 
                       portList + RPAR + SEMI
                       ) +
              CaselessLiteral("END").suppress() + 
              Optional(CaselessLiteral("ENTITY").suppress()) +
              Optional(matchPreviousLiteral(entityIdent).suppress()) + SEMI
              ).ignore(comment) + SkipTo(StringEnd()).suppress()

def combine_generic(name, arg):
    """Generate VHDL generic declaration."""
    
    if len(arg) > 1:
        return ("    %s : %s := %s" % (name, combine_type(arg[0]), str(arg[1])))
    else:
        return ("    %s : %s" % (name, combine_type(arg[0])))

def combine_generic_instance(name, values):
    """Generate VHDL generic instance."""
    
    try:
        return ("      %s => %s" % (name, str(values[name])))
    except KeyError:
        raise InstanceError("*** Generic %s not defined!" % name)

def combine_port(name, arg):
    """Generate VHDL port declaration."""
    
    return ("    %s : %s %s" % (name, arg[0], combine_type(arg[1])))

def combine_port_instance(name, values):
    """Generate VHDL port instance."""
    
    if values.has_key(name):
        return ("      %s => %s" % (name, values[name]))
    else:
        return ("      %s => open" % (name))

class EntityError(Exception):
    """Exception raised when errors detected during VHDL entity parsing.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class InstanceError(Exception):
    """Exception raised when errors detected during VHDL instance creation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class Entity(object):
    """VHDL entity parser class.
    """

    __slots__ = ('_identifier', '_generics', '_ports', '_globals')
    
    def __init__(self, filename):
        """VHDL Entity extract initialization."""
        self._identifier = ""

        fd = filename
        if isinstance(filename, basestring):
            try:
                fd = file(filename, 'r')
            except IOError:
                raise EntityError("*** File %s not found!" % filename)

        try:
            entity = entityDecl.parseFile(fd)
        except:
            raise EntityError("*** No valid entity declaration founded in file %s!" % filename)

        self._identifier = entity.identifier
        
        # Extract port information
        self._ports = dict([port[0], port[1:]] for port in entity.ports)

        # Extract generics information
        self._generics = dict([gen[0], gen[1:]] for gen in entity.generics)

        # Extract generic configuration settings
        self._globals = dict([g[0].lower(), int(g[2])] for g in entity.generics
                               if g[1][0].lower() == "integer" and len(g)>1
                            )

    def __toString(self, as_component=False):
        """Generate entity or component declaration string."""

        if not len(self._identifier):
            return ""

        if as_component:
            data = "COMPONENT "
        else:
            data = "ENTITY "
        data += self._identifier + " IS\n"

        # Add GENERIC declaration
        if len(self._generics):
            data += "  GENERIC\n  (\n"
            generics = [combine_generic(gk, gv) 
                        for gk, gv in self._generics.iteritems()]
            data += ";\n".join(generics) + "\n  );\n"

        # Add PORT declaration
        if len(self._ports):
            data += "  PORT\n  (\n"
            ports = [combine_port(pk, pv) for pk, pv in self._ports.iteritems()]
            data += ";\n".join(ports) + "\n  );\n"

        if as_component:
            data += "END COMPONENT;"
        else:
            data += "END ENTITY;"
        return data

    def __str__(self):
        return self.__toString(False)

    def asEntity(self):
        """Convert object into VHDL entity declaration string."""
        return self.__toString(False)
    
    def asComponent(self):
        """Convert object into VHDL component declaration string."""
        return self.__toString(True)

    def asInstance(self, properties=None):
        """Convert object into VHDL component instance declaration string.
        
        @param properties: contains instance settings
            properties.name ==> instance name
            properties.ports => dictionary with signal connected to each port
            properties.generics => dictionary with generics settings 
        """

        name = None
        gen_data = {}
        port_data = {}
        if properties:
            name = properties.name
            gen_data = properties.generics
            port_data = properties.ports
            
        # Creating the instance name
        if name:
            data = ("  %s : %s\n" % (name, self._identifier))
        else:
            data = ("  %s\n" % (self._identifier))

        # Adding GENERIC values if they are defined
        if len(self._generics):
            data += "    GENERIC MAP\n    (\n"
            generics = [combine_generic_instance(generic, gen_data) 
                        for generic in self._generics.keys()]
            data += ",\n".join(generics) + "\n    )\n"

        # Adding PORT values if they are defined
        if len(self._ports):
            ports = [combine_port_instance(port, port_data)
                     for port in self._ports.keys()]
            data += "    PORT MAP\n    (\n" + ",\n".join(ports) + "\n    );\n"
            
        return data

    @property
    def generics(self):
        """Get entity generics settings."""
        return self._generics
    
    @property
    def ports(self):
        """Get entity ports settings."""
        return self._ports
    
    @property
    def generics_names(self):
        """
        Returns all generic parameters names.
        """
        return self._generics.keys()

    @property
    def ports_names(self):
        """
        Returns all port names.
        """
        return self._ports.keys()

    def getWidth(self, port_name, generics):
        """Compute signal width according to generics value."""
        
        env_loc = dict([kl.lower(), int(vl)] for kl, vl in generics.iteritems()
                         if self._globals.has_key(kl.lower())
                      )
        if self._ports.has_key(port_name):
            port = self._ports[port_name][1]
            if len(port) > 1:
                left = eval(port[1].lower(), self._globals, env_loc)
                right = eval(port[3], self._globals, env_loc)
                if str(port[2]).lower() == "downto":
                    return 1 + int(left) - int(right)
                else:
                    return 1 + int(right) - int(left)
            else:
                return 1
        else:
            return 0

class InstanceInterface(object):
    """Wishbone interface management class.

    Attributes:
        iface -- Wishbone interface parameters
        parent -- VHDL instance using this interface
    """
    
    __slots__ = ("_parent", "_iface", "_errors", "_offset")

    def __init__(self, iface, parent):
        self._parent = parent
        self._iface = iface
        self._errors = self.check()
        self._offset = 0

    @property
    def signals(self):
        """Interface signals"""
        return self._iface.signals
    
    @property
    def name(self):
        """Wishbone interface name"""
        return self._iface.name
    
    @property
    def type(self):
        """Wishbone interface type"""
        return self._iface.type

    @property
    def granularity(self):
        """Address bus granularity.
        
        0 --> 8 bits (start from A0)
        1 --> 16 bits (start from A1)
        2 --> 32 bits (start from A2)
        3 --> 64 bits (start from A3)
        4 --> 128 bits (start from A4)
        """
        if self.type == "WBM":
            (_, wb_sel) = self.wb_signal("SEL")
            (wb_dat_i, wb_dat_o) = self.wb_signal("DAT")
        elif self.type == "WBS":
            (wb_sel, _) = self.wb_signal("SEL")
            (wb_dat_i, wb_dat_o) = self.wb_signal("DAT")
        else:
            return 0
        
        if wb_dat_i:
            dat_width = self._parent.port_width(wb_dat_i.name)
        elif wb_dat_o:
            wb_dat = self._parent.port_width(wb_dat_i.name)
        
        if wb_sel:
            wb_dat = wb_dat // self._parent.port_width(wb_sel.name)
            
        return wb_dat // 8
    
    @property
    def addr_width(self):
        """Return interface address bus width."""
        if self.type == "WBM":
            (_, wb_adr) = self.wb_signal("ADR")
        elif self.type == "WBS":
            (wb_adr, _) = self.wb_signal("ADR")
        else:
            wb_adr = None
            
        if wb_adr:
            return self._parent.port_width(wb_adr.name)
        else:
            return 0
    
    @property
    def data_width(self):
        """Return interface data bus width."""
        if self.type in ("WBM", "WBS"):
            (wb_dat_i, wb_dat_o) = self.wb_signal("DAT")
        
            if wb_dat_i:
                wb_dat = wb_dat_i
            else:
                wb_dat = wb_dat_o
                
            return self._parent.port_width(wb_dat.name)
        else:
            return 0

    @property
    def has_errors(self):
        """Return True if errors have been detected for this interface."""
        return len(self._iface.last_errors) > 0 or len(self._errors) > 0
    
    @property
    def last_errors(self):
        """Return errors detected for this interface during last check."""
        if len(self._iface.errors) > 0:
            return self._iface.last_errors
        return self._errors
    
    @property
    def instance_name(self):
        """Returns parent instance name."""
        return self._parent.name
    
    @property
    def offset(self):
        """Return interface base address (only valid for Slave Interfaces)."""
        return self._offset
    
    def wb_signal(self, name):
        """Search signal in interface matching with Wishbone name.
        Returns a tuple containing (in_signal, out_signal)
        """
        dir_in = None
        dir_out = None
        for (signal, hdl) in self._iface.signals.itervalues():
            if signal.type.upper() == name.upper():
                if hdl[0].lower() == "in":
                    dir_in = signal
                else:
                    dir_out = signal
        
        if dir_in is None and dir_out is None:
            return None
        return (dir_in, dir_out)
    
    def wb_signal_width(self, name):
        """Search signal in interface matching with Wishbone name.
        Returns a tuple containing (in_signal_width, out_signal_width)
        """
        dir_in = 0
        dir_out = 0
        for (signal, hdl) in self._iface.signals.itervalues():
            if signal.type.upper() == name.upper():
                if hdl[0].lower() == "in":
                    dir_in = self._parent.port_width(signal.name)
                else:
                    dir_out = self._parent.port_width(signal.name)

        return (dir_in, dir_out)
    
    def has_signal(self, name, as_input=None):
        """Check if given Wishbone signal is defined"""
        for (signal, hdl) in self._iface.signals.itervalues():
            if signal.type.upper() == name.upper():
                if as_input == None:
                    return True
                elif as_input == True and hdl[0].upper() == "IN":
                    return True
                elif as_input == False and hdl[0].upper() == "OUT":
                    return True
        return False
        
    def port_width(self, port_name):
        """Get signal width.
        
        @param port_name: name of the signal
        @return: signal width
        """
        return self._parent.port_width(port_name)
    
    def setPortCnx(self, port, signal):
        """Modify port signal name settings.
    
        @param port: port name.
        @param signal: signal name 
        """
        self._parent.setPort(port, signal)
        
    def getPortCnx(self, port):
        """Get port signal name.
    
        @param port: port name.
        """
        if port in self._parent.ports.keys():
            return self._parent.ports[port]
        return None

    def check(self):
        """Verify interface signals integrity according to instance settings."""
        
        # Verify that interface is valid
        errors = self._iface.last_errors
        if len(errors):
            return errors
        
        # No verifications for EXPORT or Clock interfaces
        if self.type in ("GLS", "WBC"):
            pass
        else:
            # Verify data busses width
            (data_in, data_out) = self.wb_signal("DAT")
            if data_in is None:
                data = self._parent.port_width(data_out.name)
            elif data_out is None:
                data = self._parent.port_width(data_in.name)
            else:
                data = self._parent.port_width(data_in.name)
                if data != self._parent.port_width(data_out.name):
                    errors.append("Input and output data buses don't have same width.")
           
            if not data in (8, 16, 32, 64, 128):
                errors.append("Interface %s, invalid data bus width => %d." % 
                              (self.name, data))
            
        self._errors = errors
        return errors


class Instance(object):
    """Defines a IP instance. Is only used for design compilation.
    There is no extra check done on parameters, they have to be checked by
    the calling piece of software.
    """
    __slots__ = ('name', 'generics', 'ports', '__base', '_ifaces', '_errors')
    
    def __init__(self, entity, name=None, generics=None, interfaces=None):
        self.name = name
        self._ifaces = {}
        self.__base = entity
        
        # Extract default generic parameters value
        self.generics = {}
        if not generics:
            generics = {}
            
        for (key, value) in self.__base.generics.iteritems():
            if generics.has_key(key):
                self.generics[key] = str(generics[key])
            elif len(value) > 1:
                self.generics[key] = str(value[1])
            
        # Extract Wishbone interfaces
        if interfaces:
            self._ifaces = dict([k, InstanceInterface(v, self)] 
                                for k, v in interfaces.iteritems())

        # Initialize ports
        self.ports = {}
        
        # Checking for errors
        self._errors = self.check()
    
    @property
    def has_errors(self):
        """Return True if errors have been detected for this interface."""
        return len(self._errors) > 0
    
    @property
    def last_errors(self):
        """Return errors detected for this interface during last check."""
        return self._errors
    
    @property
    def entity(self):
        """Get entity declaration."""
        return self.__base
    
    def interface(self, if_name):
        """Get interface information.
        
        @param if_name: interface name
        @return: InstanceInterface object containing interface settings.
        """
        return self._ifaces[if_name]
    
    @property
    def interfaces(self):
        """Get all interfaces."""
        return self._ifaces
    
    def port_width(self, port_name):
        """Get signal width according to instance generic values.
        
        @param port_name: name of the signal
        @return: signal width
        """
        return self.__base.getWidth(port_name, self.generics)
    
    @property
    def port_names(self):
        """Return a list containing signal names."""
        
        return self.__base.ports_names
    
    def setPorts(self, ports):
        """Update/modify ports settings."""
        
        valid_keys = self.__base.ports_names
        for key,value in ports.iteritems():
            if key in valid_keys:
                self.ports[key] = value
    
    def setPort(self, key, value):
        """Update/modify ports settings."""
        if key in self.__base.ports_names:
            self.ports[key] = value

    def setGenerics(self, generics):
        """Update/modify generics settings."""
        
        valid_keys = self.__base.generics_names
        for key,value in generics.iteritems():
            if key in valid_keys:
                self.generics[key] = value

    def setOffset(self, if_name, offset=0):
        """Update/modify interface base address.
        
            @param if_name: interface name
            @param offset: new base address.
        """
        self._ifaces[if_name]._offset = int(offset)

    def __str__(self):
        return self.__base.asInstance(self)

    @property
    def asComponent(self):
        """Convert object into VHDL component declaration string."""
        return self.__base.asComponent()
    
    def check(self):
        """Check instance interfaces for errors.
        
        @return: list containing detected errors
        """
        errors = []
        for iface in self._ifaces.itervalues():
            errors.extend(iface.check())
            
        self._errors = errors
        return errors
        
def main():
    """
    Main function, deals with arguments and launch program
    """
    entity = Entity(filename='../../temp/imx_wrapper.vhd')
    print entity
    print "Generics for imx_wrapper:"
    print entity.generics_names
    entity = Entity(filename='../../temp/servo_mngr.vhd')
    print entity
    print entity.asComponent()
    instance = Instance(entity)
    instance.name = "bob"
    print instance
    print entity.generics_names


if __name__ == '__main__':
    main()
