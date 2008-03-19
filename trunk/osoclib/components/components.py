#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     Components.py
# Purpose:  HDL Components manipulation routines
#
# Author:   Fabrice MOUSSET
#
# Created:  2007/10/24
# Licence:  GPLv3 or newer
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

__doc__         = "HDL Components manipulation routines"
__version__     = "1.0"
__versionTime__ = "24/10/2007"
__author__      = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os, sys
import os.path as dir

if __name__ == "__main__":
    # Add base library to load path
    dirname, base = dir.split(dir.dirname(dir.realpath(__file__)))
    sys.path.append(dirname)

from core import XmlFileBase, ZipFile, ZipString, is_zipfile
from vhdl import Entity
from StringIO import StringIO
import string

# WB_SIGNALS define wishbone signals aliases
WB_SIGNALS = {
    "RST" : "RST", "RESET" : "RST",
    "CLK" : "CLK", "CLOCK" : "CLK",
    "ADR" : "ADR", "ADDR"  : "ADR", "ADDRESS"  : "ADR",
    "DAT" : "DAT", "DATA"  : "DAT", "READDATA" : "DAT", "WRITEDATA" : "DAT",
    "WE"  : "WE",
    "SEL" : "SEL",
    "ACK" : "ACK",
    "CYC" : "CYC", "CYCLE" : "CYC",
    "STB" : "STB"
}

# WB_SIGNALS define wishbone interfaces type and corresponding signal with direction
WB_INTERFACES = {
    "GLS" : ("Global", {}),
    "WBM" : ("Wishbone Master", {"ADR":"O", "DAT":"IO", "WE":"O", "SEL":"O", "ACK":"I", "CYC":"O", "STB":"O"}),
    "WBS" : ("Wishbone Slave",  {"ADR":"I", "DAT":"IO", "WE":"I", "SEL":"I", "ACK":"O", "CYC":"I", "STB":"O"}),
    "WBC" : ("Wishbone Clock and Reset", {"RST":"IO", "CLK":"IO"})
}

# COMPONENTS_NODES define Component XML file sections and attributs
COMPONENTS_NODES = {
    "hdl_files"     : ("name", "scope", "order", "istop"),
    "driver_files"  : ("name", "scope"),
    "generics"      : ("name", "type", "value", "valid"),
    "registers"     : ("name", "offset", "width"),
    "ports"         : ("name", "interface", "type"),
    "interfaces"    : ("name", "type", "clockandreset")
}

def getSignalAttributs(signal):
    """Extract signal informations. The signal name must match folowing maning convention:
    
    type_name_signal
  
        type = Wishbone interface type. Default = Global (GLS).
        name = Interface name. Default = default.
        signal = Signal name.
                
    Returns a tulpe containing (type, name, signal)   
    """
    
    name = string.split(str(signal).upper(), '_')
    
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
            if WB_SIGNALS.has_key(name[1]):
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
    if wb_signal:
        if if_signals.has_key(wb_signal):
           return (wb_interface, wb_name, wb_signal)

        if WB_INTERFACES["WBC"][1].has_key(wb_signal):
            if wb_name.startswith(wb_interface):
                return ("WBC", "_".join([wb_name, "clockandreset"]), wb_signal)
            return ("WBC", "_".join([wb_interface, wb_name, "clockandreset"]), wb_signal)
        
        wb_name = None

    return (wb_interface, wb_name, None)


# COMPONENTS_ATTRIBS define XML base node attributes
COMPONENTS_ATTRIBS = {"name":"", "version":"", "category":""}

class ComponentError(Exception):
    """Exception raised when errors detected during component management.

    Attributs:
        message -- textual explanation of the error
    """

    __slots__ = ['message']

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class Component(XmlFileBase):
    """Components managment class.

    Attributes:
        filename -- Name of Zip archive which describe/include a component
    """
    archive_name = None
    xml_basename = "component"
    filename = None
    __xml_name = "description.xml"

    def __init__(self, filename=None):
        # Open ZipFile in RAM, so we can modify the archive without loosing previous datas.
        self.zfp = ZipString(filename)
        xml_data = ""

        # Scan Zipfile to find XML descriptor
        for name in self.zfp.namelist():
            if name.lower().endswith('.xml'):
                xml_data = self.zfp.read(name)
                self.__xml_name = name
                break

        XmlFileBase.__init__(self, COMPONENTS_NODES, COMPONENTS_ATTRIBS, None, xml_data)
        if filename:
            self.filename = dir.basename(filename)

    def save(self, filename=None):
        """Update component settings in archive."""

        # Update XML description in archive
        self.zfp.updatestr(self.__xml_name, self.asXML())

        # Save to disk if file specified
        if filename:
            self.zfp.saveAs(filename)

    def setTop(self, name):
        """Define IP top file."""

        is_possible = False
        for file in self.hdl_files:
            if file.name == name:
                is_possible = True
                break

        if not is_possible:
            raise ComponentError("*** File '%s' dont exist in component, operation canceled.\n" % name)

        # Erase previous generics, ports and interfaces
        self.generics.clear()
        self.ports.clear()
        self.interfaces.clear()

        # Extract Top fil entity declaration
        hdl = Entity(StringIO(self.zfp.read(name)))

        # Add new Generics and Ports values
        for generic in hdl.generics:
            if len(generic) > 2:
                self.generics.add(text=None, name=generic[0], type=generic[1], value=generic[2])
            else:
                self.generics.add(text=None, name=generic[0], type=generic[1])

        # parsing signals to extract interfaces
        interfaces = {}
        clocks = []
        for port in hdl.ports:
            # Extracting interface type, name and signal 
            (wb_type, if_name, wb_signal) = getSignalAttributs(port[0])

            # Adding interface to list
            if not interfaces.has_key(if_name):
                interfaces[if_name] = [wb_type]
                if wb_type == "WBC":
                    clocks.append(if_name.upper())

            # Checking interface name validity
            if interfaces[if_name][0] != wb_type:
                raise ComponentError("*** Error during top file signals parsing. Duplicate interface name '%s'\n" % if_name)
            
            if not wb_signal:
                raise ComponentError("*** Error during top file signals parsing. Unknown signal '%s'\n" % port)
            
            # Saving interface in current list
            interfaces[if_name].append(port[0])
            
            # Adding signal to XML file
            self.ports.add(text=None, name=port[0], interface=if_name, type=wb_signal)
        
        # parsing interfaces to extract clock and reset signals
        for (key,value) in interfaces.items():
            if key.upper() in clocks:
                self.interfaces.add(text=None, name=key, type=value[0])
            else:
                clock = None
                if len(clocks) == 1:
                    clock = clocks[0]
                else:
                    for clk in clocks:
                        if clk.startswith(key.upper()):
                            clock = clk
                
                self.interfaces.add(text=None, name=key, type=value[0], clockandreset=clock)
    
    def addHdl(self, filename, scope="all", order=0, istop=0):
        """Append new HDL file to component.

            filename = new HDL file to add to this IP
            scope = Scope of this file. By default 'all'.
            order = load order. By default index of the file.
            istop = to declare this file as top entity. By default False.
        """

        # First check if file exist
        if not os.path.isfile(filename):
            raise ComponentError("*** File '%s' not found, file addition canceled.\n" % filename)

        # Then get base name and directory and check if file already included
        name = dir.basename(filename)
        dirname = dir.dirname(dir.realpath(filename))
        for file in self.hdl_files:
            if file.name == name:
                raise ComponentError("*** File '%s' already exist in component, file addition canceled.\n" % name)

        # Then adjust file load order
        if order >= len(self.hdl_files):
            order = len(self.hdl_files) + 1

        if order == 0:
            order = len(self.hdl_files) + 1

        # Now we push down every file that has to loaded after this file
        for file in self.hdl_files:
            if file.order >= order:
                file.order += 1

        # Finally add this file to XML description and to ZIP archive
        self.hdl_files.add(None, name=name, scope=scope, order=order, istop=istop)
        self.zfp.update(name, dir.join(dirname, name))

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
        isTop = False
        for file in self.hdl_files:
            if file.name == filename:
                order = file.order
                istop = file.istop
                self.hdl_files.remove(file)
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
        for file in self.hdl_files:
            if file.order >= order:
                file.order -= 1
