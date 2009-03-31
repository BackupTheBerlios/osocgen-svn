#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Components.py
# Purpose:  HDL Components manipulation routines
#
# Author:   Fabrice MOUSSET
#
# Created:  2007/10/24
# License:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Last commit info:
# ----------------------------------
# $LastChangedDate:: xxxx/xx/xx xx:xx:xx $
# $Rev::                                 $
# $Author::                              $
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

"Orchestra Components/IP manipulation routines and classes."

__version__     = "1.0"
__versionTime__ = "24/10/2007"
__author__      = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os, sys
import os.path as path

if __name__ == "__main__":
    # Add base library to load path
    dirname, base = path.split(path.dirname(path.realpath(__file__)))
    sys.path.append(dirname)

from core import XmlFileBase, ZipString, to_boolean, cmp_stri
from core import WB_SIGNALS, WB_INTERFACES
from vhdl import Entity, EntityError, Instance, InstanceError, combine_type
from StringIO import StringIO

def check_xml_entity(entity, interfaces, ports):
    """Check if entity corresponds to XML declaration.
    
    @param entity: VHDL entity declaration
    @param generics: generics assignments
    @param ports: ports assignments
        
    @return: list of errors.
    """
    
    errors = []
    
    # Get component interfaces
    ifaces = {}
    for iface in interfaces.iteritems():
        ifaces[iface.name.lower()] = 0
        
    # Get component ports
    cp_ports = {}
    for port in ports.iteritems():
        cp_ports[port.name.lower()] = False

    # Check entity ports declaration
    for hdl_port_name in entity.ports.keys():
        hdl_port_name = hdl_port_name.lower()
        if cp_ports.has_key(hdl_port_name):
            cp_ports[hdl_port_name] = True
            port = ports.getElement(hdl_port_name)[0]
            port_iface_name = port.interface.lower()
            if not ifaces.has_key(port_iface_name):
                errors.append("*** Port '%s' use undeclared interface '%s'." % 
                              (port.name, port.interface))
            else:
                ifaces[port_iface_name] += 1
        else:
            errors.append("*** Port '%s' not declared in XML descriptor." %
                           hdl_port_name)
        
    # Verify that each interface has signal attached
    for (ifname, ifsignals) in ifaces.iteritems():
        if ifsignals == 0:
            errors.append("*** Interface '%s' has not signal attached." %
                          ifname)
        
    # Verify that each port is present in HDL top file
    for (port, port_ok) in cp_ports.iteritems():
        if not port_ok:
            errors.append("*** Port '%s' don't exist in Top entity declaration." %
                           port)
    
    return errors

def find_component(basedir, name):
    """Find component based on his name.
    
    @param basedir: components directory
    @param name: component to find
    """
    if isinstance(basedir, basestring) and isinstance(name, basestring):
        for cp_file in os.listdir(basedir):
            filename = path.join(basedir, cp_file)
            if(path.isfile(filename)):
                cp = Component(filename)
                if cp.name.lower() == name.lower():
                    return cp
    
    return None

def split_signal(signal):
    """Extract signal informations. The signal name must match following naming
    convention:
            type_name_signal
    
    where:
        type = Wishbone interface type. Default = Global/Export (GLS).
        name = Interface name. Default = default.
        signal = Signal name.
    
    @param signal: signal name to analyze
    @return: tuple containing (wb_type, wb_name, signal)   
    """
    
    name = str(signal).upper().split('_')
    
    # Only one substring, testing if it is a Clock&Reset interface signal
    if len(name) == 1:
        if WB_SIGNALS.has_key(signal):
            wb_signal = WB_SIGNALS[signal]
            if WB_INTERFACES["WBC"][1].has_key(wb_signal):
                return ("WBC", "default", wb_signal)
        
        return ("GLS", "export", "export")
    
    wb_signal = None
    wb_interface = None
    wb_name = None

    # Extracting interface type
    if WB_INTERFACES.has_key(name[0]):
        wb_interface = name[0]

    if wb_interface:
        if len(name) == 2:
            if wb_interface == "GLS":
                return ("GLS", "export", "export")
            elif WB_SIGNALS.has_key(name[1]):
                wb_signal = WB_SIGNALS[name[1]]
                wb_name = wb_interface + "_noname"
        else:
            if WB_SIGNALS.has_key(name[2]):
                wb_signal = WB_SIGNALS[name[2]]
                wb_name = name[1]
            elif WB_SIGNALS.has_key(name[1]):
                wb_signal = WB_SIGNALS[name[1]]
                wb_name = wb_interface + "_noname"
    else:
        if WB_SIGNALS.has_key(name[0]):
            wb_signal = WB_SIGNALS[name[0]]
            if WB_INTERFACES["WBC"][1].has_key(wb_signal):
                return ("WBC", "default", wb_signal)
            
        return ("GLS", "export", "export")
    
    if_signals = WB_INTERFACES[wb_interface][1]
    if not wb_signal is None:
        if if_signals.has_key(wb_signal):
            return (wb_interface, wb_name, wb_signal)

        if WB_INTERFACES["WBC"][1].has_key(wb_signal):
            if wb_name.startswith(wb_interface):
                return ("WBC", "_".join([wb_name, "clockandreset"]), wb_signal)
            return ("WBC", "_".join([wb_interface, wb_name, "clockandreset"]), wb_signal)
        
        wb_name = None

    return (wb_interface, wb_name, None)

class WishboneInterface(object):
    """Wishbone interface management class.

    @param iface:  Wishbone interface parameters
    @param signals: Signals attached to this interface
    @param hdl: VHDL entity declaration
    """
    __slots__ = ("iface", "signals", "_errors", "wb_signals", "wb_descr")

    def __init__(self, iface=None, signals=None, hdl=None):
        if iface==None:
            return
        self.iface = iface
        self.signals = {}
        for signal in signals:
            name = signal.name.lower()
            self.signals[name] = (signal, hdl.ports[name])
        
        self._errors = []
        try:
            (self.wb_descr, self.wb_signals) = WB_INTERFACES[iface.type.upper()]
        except KeyError:
            self.wb_descr = "Unknown!!!!"
            self.wb_signals = None
            self._errors.append("Interface '%s', unknown type '%s'" % 
                               (iface.name, iface.type))
        
    @property
    def name(self):
        """Wishbone interface name"""
        return self.iface.name.lower()
    
    @property
    def type(self):
        """Wishbone interface type"""
        return self.iface.type.upper()

    @property
    def has_errors(self):
        """Return True if errors have been detected for this interface."""
        return len(self._errors) > 0
    
    @property
    def last_errors(self):
        """Return errors detected for this interface during last check."""
        return self._errors
    
    def wb_signal(self, name):
        """Search in and out signal in interface matching with Wishbone name.
        
        @param name: signal name
        @return: tuple containing (in_signal, out_signal)
        """
        dir_in = None
        dir_out = None
        for (signal, hdl) in self.signals.itervalues():
            if signal.type.upper() == name.upper():
                if hdl[0].lower() == "in":
                    dir_in = signal
                else:
                    dir_out = signal
        
        return (dir_in, dir_out)
    
    def check(self):
        """Verify interface integrity. Populate errors when errors detected."""
        
        if self.wb_signals == None:
            return self._errors
        
        errors = []
        if self.type == "GLS":
            # All external signals are correct
            pass
        elif self.type == "WBC":
            # Wishbone clock interface
            signal_avail = {}
            for (signal, port_info) in self.signals.itervalues():
                if signal.type.upper() in self.wb_signals.keys():
                    if_type = port_info[0].lower()
                    if signal.type.upper() in signal_avail.keys():
                        errors.append("%s interface '%s', multiple %s signals specified." % 
                                      (self.wb_descr, self.name, signal.type))
                    elif ((not if_type in signal_avail.values()) 
                          and len(signal_avail)>0):
                        errors.append("%s interface '%s', clock and reset must be in same direction." % 
                                      (self.wb_descr, self.name))
                    else:
                        signal_avail[signal.type.upper()] = if_type
                else:
                    errors.append("%s interface '%s', unknown type '%s' for signal %s." % 
                                  (self.wb_descr, self.name, signal.type, signal.name))
    
        else:
            # Wishbone Master/Slave interface
            iface_avail = {}
            for signal in self.wb_signals.keys():
                iface_avail[signal] = []

            for (signal, port_info) in self.signals.itervalues():
                if signal.type.upper() in self.wb_signals.keys():
                    if port_info[0].lower() in ("in", "out"):
                        if_type = port_info[0][0].upper()
                        if if_type in iface_avail[signal.type.upper()]:
                            errors.append("%s interface '%s', duplicate %s signal %s." % 
                                          (self.wb_descr, self.name, 
                                           port_info[0].upper(), signal.name))
                        else:
                            iface_avail[signal.type.upper()].append(if_type)
                    else:
                        errors.append("%s interface '%s', unknown direction for signal %s." % 
                                  (self.wb_descr, self.name, signal.name))
                else:
                    errors.append("%s interface '%s', unknown type '%s' for signal %s." % 
                              (self.wb_descr, self.name, signal.type, signal.name))
    
            for k, v in self.wb_signals.iteritems():
                avail = iface_avail[k]
                if len(avail) == 0:
                    if v.islower():
                        pass
                    else:
                        errors.append("%s interface '%s', no signal '%s' declared." % 
                                      (self.wb_descr, self.name, k))
                else:
                    for direc in v:
                        if direc.islower():
                            pass
                        elif not direc in avail:
                            if direc == "I":
                                dir_str = "input"
                            else:
                                dir_str = "output"
                            
                            errors.append("%s interface '%s', no %s signal '%s' declared." % 
                                          (self.wb_descr, self.name, dir_str, k))
        
        self._errors = errors
        return errors
    
class ComponentError(Exception):
    """Exception raised when errors detected during component management.

    @param message: textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

# COMPONENTS_NODES define Component XML file sections and attributes
COMPONENTS_NODES = {
    "hdl_files"     : ("name", "scope", "order", "istop"),
    "driver_files"  : ("name", "scope"),
    "generics"      : ("name", "type", "value", "valid"),
    "registers"     : ("name", "offset", "width"),
    "ports"         : ("name", "interface", "type"),
    "interfaces"    : ("name", "type", "clockandreset")
}

# COMPONENTS_ATTRIBS define XML base node attributes
COMPONENTS_ATTRIBS = {"name":"", "version":"", "category":""}

class Component(XmlFileBase):
    """Components management class.

    @param filename: Name of Zip archive which describe/include a component
    """
    archive_name = None
    xml_basename = "component"
    filename = None
    __xml_name = "description.xml"
    _wb_ifaces = {}
    _errors = {}

    @property
    def has_errors(self):
        """Is true, if there are errors detected during last check."""
        return len(self._errors) > 0
    
    @property
    def last_errors(self):
        """Returns errors detected during last check."""
        return self._errors
    
    def __init__(self, filename=None):
        # Open ZipFile in RAM, so we can modify the archive without loosing previous data.
        self.zfp = ZipString(filename)
        xml_data = ""

        # Scan Zipfile to find XML descriptor
        for name in self.zfp.namelist():
            if name.lower().endswith('.xml'):
                xml_data = self.zfp.read(name)
                self.__xml_name = name
                break

        XmlFileBase.__init__(self, COMPONENTS_NODES, COMPONENTS_ATTRIBS, None, xml_data)
        if not filename is None:
            self.filename = path.basename(filename)

        # HDL files attributes clean-up
        for hdl_file in self.hdl_files.iteritems():
            hdl_file.order = int(hdl_file.order)
            hdl_file.istop = to_boolean(hdl_file.istop)
        
        # Interfaces attributes clean-up
        for iface in self.interfaces.iteritems():
            iface.type = str(iface.type).upper()
            iface.name = str(iface.name).lower()
        
        # Signals attributes clean-up
        for port in self.ports.iteritems():
            port.name = str(port.name).lower()

        # Generics attributes clean-up
        for generic in self.generics.iteritems():
            generic.name = str(generic.name).lower()
            
        # Perform component valid check
        self.check()

    def save(self, filename=None):
        """Update component settings in archive."""

        # Update XML description in archive
        self.zfp.updatestr(self.__xml_name, self.asXML())

        # Save to disk if file specified
        if not filename is None:
            self.zfp.saveAs(filename)

    def setTop(self, name):
        """Define IP top file."""

        is_possible = False
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.name == name:
                is_possible = True
                break

        if not is_possible:
            raise ComponentError("*** File '%s' don't exist in component, operation canceled.\n" % name)

        # Extract Top file entity declaration
        try:
            hdl = Entity(StringIO(self.zfp.read(name)))
        except EntityError:
            raise ComponentError("*** File '%s' has no valid entity declaration, operation canceled.\n" % name)

        # Erase previous generics, ports and interfaces
        self.generics.clear()
        self.ports.clear()
        self.interfaces.clear()

        # Add new Generics and Ports values
        for (name, attr) in hdl.generics.iteritems():
            gen_type = combine_type(attr[0])
            if len(attr) > 1:
                self.generics.add(name=name, type=gen_type, value=attr[1])
            else:
                self.generics.add(name=name, type=gen_type)

        # parsing signals to extract interfaces
        interfaces = {}
        clocks = []
        for port in hdl.ports.keys():
            # Extracting interface type, name and signal 
            (wb_type, if_name, wb_signal) = split_signal(port)

            # Adding interface to list
            if not interfaces.has_key(if_name):
                interfaces[if_name] = [wb_type]
                if wb_type == "WBC":
                    clocks.append(if_name.upper())

            # Checking interface name validity
            if interfaces[if_name][0] != wb_type:
                raise ComponentError("*** Error during top file signals parsing. Duplicate interface name '%s'\n" % if_name)
            
            if wb_signal is None:
                raise ComponentError("*** Error during top file signals parsing. Unknown signal '%s'\n" % port)
            
            # Saving interface in current list
            interfaces[if_name].append(port)
            
            # Adding signal to XML file
            self.ports.add(name=port, interface=if_name, type=wb_signal)
        
        # parsing interfaces to extract clock and reset signals
        for (key, value) in interfaces.items():
            if key.upper() in clocks:
                self.interfaces.add(name=key, type=value[0])
            else:
                clock = None
                if len(clocks) == 1:
                    clock = clocks[0]
                else:
                    for clk in clocks:
                        if clk.startswith(key.upper()):
                            clock = clk
                
                self.interfaces.add(name=key, type=value[0], clockandreset=clock)
    
    def getAttached(self, name, interface=False):
        """Search all signals attached to a given interface.
        
        Attributes:
            name - interface name
            interface - if true, seach for attached interfaces else for signals
            
        returns: (iface, list)
            iface - interface properties
            list - list of attached signals or interfaces.
        """
        name = name.lower()
        src = self.interfaces.getElement(name)
        if src is None:
            raise ComponentError("*** No interface '%s' found, operation canceled.\n" % name)

        src = src[0]
        attached = []
        if interface:
            if src.type.lower() == "wbc":
                attached = [iface for iface in self.interfaces.iteritems()
                                if cmp_stri(iface.clockandreset, name)
                           ]
        else:
            attached = [port for port in self.ports.iteritems()
                            if port.interface.lower() == name
                        ]
                    
        return (src, attached)
    
    def addHdl(self, filename, scope="all", order=0, istop=False):
        """Append new HDL file to component.

            filename = new HDL file to add to this IP
            scope = Scope of this file. By default 'all'.
            order = load order. By default index of the file.
            istop = to declare this file as top entity. By default False.
        """

        # First check if file exist
        if not path.isfile(filename):
            raise ComponentError("*** File '%s' not found, file addition canceled.\n" % filename)

        # Then get base name and directory and check if file already included
        name = path.basename(filename)
        dir_name = path.dirname(path.realpath(filename))
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.name == name:
                raise ComponentError("*** File '%s' already exist in component, file addition canceled.\n" % name)

        # Then adjust file load order
        if order >= len(self.hdl_files):
            order = len(self.hdl_files) + 1

        if order == 0:
            order = len(self.hdl_files) + 1

        # Now we push down every file that has to loaded after this file
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.order >= order:
                hdl_file.order += 1

        # Finally add this file to XML description and to ZIP archive
        self.hdl_files.add(name=name, scope=scope, order=order, istop=istop)
        self.zfp.update(name, path.join(dir_name, name))

        # Hmmm, not finished if this file is the Top Entity
        if istop:
            self.setTop(name)

    def removeHdl(self, filename):
        """Remove HDL file from the component.

            filename = Name of the HDL file.
        """

        # Look if this file exist or not
        filename = str(filename).lower()
        order = None
        istop = False
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.name == filename:
                order = hdl_file.order
                istop = hdl_file.istop
                self.hdl_files.remove(hdl_file)
                break

        if order is None:
            raise ComponentError("*** File '%s' don't exist in component, file suppression canceled.\n" % filename)

        # Delete file from Zip archive
        try:
            self.zfp.removeFile(filename)
        except:
            pass

        # if this was the top entity, remove generics and ports declaration
        if istop:
            self.generics.clear()
            self.ports.clear()
            self.interfaces.clear()

        # and finally remove the file from the XML description
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.order >= order:
                hdl_file.order -= 1

    def extractHDL(self, base_dir, context=None):
        """Copy components HDL files to a given directory.
        
            @param base_dir: destination directory
            @param context: used to define type of project (xilinx, altera, etc.)
            @return:  list containing file names
        """
        #TODO: Extract file base on context value
        files = []
        for hdl_file in self.hdl_files.iteritems():
            files.append(hdl_file.name)
            filename = path.join(base_dir, hdl_file.name)
            try:
                vhdl_fd = open(filename, "wb")
            except IOError:
                raise ComponentError("Can't create %s file." % hdl_file.name)
            
            vhdl_fd.write(self.zfp.read(hdl_file.name))
            vhdl_fd.close()
        return files
        
    def check(self):
        """Verify component integrity."""
        
        # First search top entity
        topFile = None
        errors = []
        for hdl_file in self.hdl_files.iteritems():
            if hdl_file.istop:
                if not topFile is None:
                    errors.append("*** Multiple top entity declaration ('%s' and '%s')."%(topFile,hdl_file.name))
                topFile = hdl_file.name
        
        hdl = None
        if not topFile:
            errors.append("No Top entity declaration.")
        else:
            # Extract Top file entity declaration
            topFileStr = StringIO(self.zfp.read(topFile))
            try:
                hdl = Entity(topFileStr)
            except EntityError:
                errors.append("Entity declaration parsing error.")

        self._wb_ifaces = {}
        if hdl:
            # Verify entity signals
            errors.extend(check_xml_entity(hdl, self.interfaces, self.ports))
            
            # Verify interfaces signals
            for iface in self.interfaces.iteritems():
                (_, signals) = self.getAttached(iface.name)
                if_name = iface.name.lower()
                wb_if = WishboneInterface(iface, signals, hdl)
                self._wb_ifaces[if_name] = wb_if
                errors.extend(wb_if.check())
                
        # Verify that declared file is present in archive
        namelist = self.zfp.namelist()
        for hdl_file in self.hdl_files.iteritems():
            try:
                namelist.index(hdl_file.name)
            except ValueError:
                errors.append("*** File '%s' don't exist in archive." % hdl_file.name)
        
        self._errors = errors
        return errors
    
    # pylint: disable-msg=W0622
    def addInterface(self, name=None, type="export", clockandreset=None):
        """Add new interface to component.
        
            name = interface name
            type = type of interface (WBM, WBC, WBS or export) 
            clockandreset = interface clock domain
        """
        
        # Check parameters
        if not name:
            raise ComponentError("*** Parameter error, no interface name specified.")
        name = name.lower()
        
        if not type:
            raise ComponentError("*** Parameter error, no interface type specified.")

        type = str(type).upper()

        if not WB_INTERFACES.has_key(type):
            raise ComponentError("*** Parameter error, unknown interface type '%s'." % type)

        if (type=="WBS" or type=="WBM"):
            if clockandreset==None:
                raise ComponentError("*** Parameter error, interface type '%s' need clockandreset interface." % type)
            clockandreset = clockandreset.lower()
            
        # Check if there is no interface with same name
        if self.interfaces.hasElement(name):
            raise ComponentError("*** Parameter error, interface name '%s' already defined." % name)
        
        self.interfaces.add(name=name, type=type, clockandreset=clockandreset)
            
    def delInterface(self, name=None):
        """Remove interface from component.
        
            name = interface name
        """

        if not self.interfaces.hasElement(name):
            raise ComponentError("*** Parameter error, no interface '%s' exist." % name)
        
        self.interfaces.remove(name)

    def cleanInterfaces(self):
        """Remove unused interfaces from component XML file.
        """
        # Get component interfaces
        ifaces = {}
        for iface in self.interfaces:
            ifaces[iface[0].name.lower()] = 0

        # Check to entity ports declaration
        for port in self.ports.iteritems():
            port_iface_name = port.name.lower()
            if ifaces.has_key(port_iface_name):
                ifaces[port_iface_name] += 1
            
        # Verify that each interface has signal attached
        for (ifname, ifsignals) in ifaces.iteritems():
            if ifsignals == 0:
                self.interfaces.remove(ifname)
    
    def asEntity(self, context=None):
        """Convert component into VHDL entity object.
        """
        # First search top entity
        for hdl_file in self.hdl_files.iteritems():
            #TODO: Extract entity value based on context value
            if hdl_file.istop:
                # Extract Top file entity declaration
                topFileStr = StringIO(self.zfp.read(hdl_file.name))
                try:
                    return Entity(topFileStr)
                except EntityError:
                    raise ComponentError("No entity declaration in top file.")
        
        raise ComponentError("No top file specified.")

    def asInstance(self, name, generics):
        """Convert component into project instance object.
        
        @param name: instance name
        @generics: VHDL generics parameters values
        """
        try:
            return Instance(entity=self.asEntity(), name=name, 
                            generics=generics, 
                            interfaces=self._wb_ifaces)
        except InstanceError:
            raise ComponentError("Instance %s of %s creation error." %
                                 (name, self.name))
