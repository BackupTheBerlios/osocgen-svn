#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     top.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2000/02/04
# License:  GPLv3 or newer
#=============================================================================
# Revision list :
#
# Date       By        Changes
#
#=============================================================================

__doc__ = \
"""This script will be able to generate Top module for an Orchestra system.
"""
__version__ = "$Id$"
__versionTime__ = "04/02/2009"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2009 Fabrice MOUSSET"

import os.path as path
from StringIO import StringIO
from entity import Entity, Instance
from utils import make_header, _VHDL_ARCHITECTURE, to_bit_vector
from utils import to_comment, signal_name, combine_type
from syscon import make_syscon, SysconError
from intercon import make_intercon, InterconError

class TopError(Exception):
    """Exception raised when errors detected during Package manipulation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

def port_declaration(iface, signal, name=None):
    """Generate VHDL port signal declaration for entity.
    
        @param iface: Wishbone interface settings (vhdl.Interface)
        @param signal: VHDL signal declaration sequence
        @param name: default port name
    """
    if signal[1][0].upper() == "IN":
        pdir = "_o"
        port_type = "out "
    else:
        pdir = "_i"
        port_type = "in "
    
    if name == None:
        name = iface.name

    port_name = signal_name(name, signal[0].type + pdir)
    port_type += combine_type(signal[1][1], iface.port_width(signal[0].name))
    return (port_name.lower(), port_type.lower())

def port_matrix(iface, signal):
    """Generate port signal settings.
    """
    name = signal[0].name
    names = [name]
    if signal[1][0].upper() == "IN":
        names.append("to")
    elif signal[1][0].upper() == "OUT":
        names.append("from")
    else:
        names.append("fromandto")

    names.append(iface._parent.name)
    port_name = "_".join(names)
        
    # Connecting signals to interface
    iface.setPortCnx(name, port_name)    

    # Returning value
    port_type = combine_type(signal[1][1], iface.port_width(signal[0].name))
    return (port_name.lower(), (signal[1][0], port_type.lower()))

def mk_signal(iface, signal, vhdl):
    name = "_".join([iface._parent.name, signal])
    iface.setPortCnx(signal, name)
    return (name, combine_type(vhdl[1][1], iface.port_width(signal)))

def make_top(project):
    """Generate Top module for given project.
    
        @param project: project settings
        @return: vhdl.Entity instance from top module
    """

    # 1. Create RESET synchronization module
    hdl_files = []
    try:
        clk_hdl, fname = make_syscon(project.path)
        hdl_files.append(fname)
    except SysconError, e:
        raise TopError(e.message)
    
    # 1.1 Create Clock synchronization instance and connect RESET signal
    clk_ip = Instance(clk_hdl)
    clk_ip.setPort("reset_ext", "reset")
    
    # 2. Create IP connection signals
    elmts = []
    for _, iface in project.wires.iteritems():
        elmts.extend(iface[0])
        elmts.extend(iface[1])

    signals = dict(mk_signal(iface, sig, vhdl) for iface in elmts
                        for sig, vhdl in iface.signals.iteritems())
        
    # 2.1 Add reset/clock signals
    for name, ifaces in project.clocks.iteritems():
        clk_name = name
        rst_name = name + "_sync_reset"
        signals[rst_name] = "std_logic"
        for iface in ifaces:
            for sigs in iface.signals.itervalues():
                xml = sigs[0]
                if xml.type == "CLK":
                    iface.setPortCnx(xml.name, clk_name)
                if xml.type == "RST":
                    iface.setPortCnx(xml.name, rst_name)

    # 3. Create address decoder module for each wishbone master interface
    intercons = []
    try:
        for (name, ifaces) in project.wires.iteritems():
            masters, slaves = ifaces[0], ifaces[1]
            if len(masters) > 1:
                raise TopError("Cannot generate multi-master '%s' bus." % name)
            master = masters[0]
            entity, fname = make_intercon(name, project.path, master, slaves)
            intercons.append(entity)
            hdl_files.append(fname)
            
    except InterconError, e:
        raise TopError(e.message)

    # 4. Now we create top file
    fname = ("%s.vhd" % project.name)
    hdl_files.append(fname)
    try:
        top_file = open(path.join(project.path, fname), "w")
    except IOError:
        raise TopError("Can't create output files '%s'." % fname)
    
    top_file.write(make_header("IP top module", project.name))
    
    # 5. Building entity declaration
    entity = "entity %s is\n" % project.name
    entity += "  port (\n"
    entity += "    -- Clock(s) signals\n"

    entity_clocks =  dict((name, "std_logic")
                            for name, _ in project.clocks.iteritems()
                        )
    ports = ["    %s : in %s" % (key, value) 
                for key, value in entity_clocks.iteritems()
            ]
    
    entity_ports = {}
    entity += "    reset : in std_logic;\n"
    entity += "\n".join(ports)
    
    for iface in project.externals:
        entity += ";\n\n    -- External signals for %s\n" % iface.name
        iface_ports =  dict(port_matrix(iface, signal) 
                                for _, signal in iface.signals.iteritems()
                                )
        ports = ["    %s : %s %s" % (key, value[0], value[1]) 
                    for key, value in iface_ports.iteritems()
                ]
       
        entity += ";\n".join(ports)
        
        # Add port signals to port list
        entity_ports.update(dict((key, value[1]) 
                    for key, value in iface_ports.iteritems()))
        
    entity += "\n  );"
    entity += "\nend entity;\n"

    top_file.write(entity)
    
    # 2. Create architecture
    top_file.write(_VHDL_ARCHITECTURE % (project.name))
    
    # 2.1 Add interconnection signals
    top_file.write(to_comment(['Interconnection signals']))
    signal = ["signal %s : %s" % (sig_name, sig_type) 
                for sig_name, sig_type in signals.iteritems()
              ]
    top_file.write("  %s;\n" % ";\n  ".join(signal))

    # 2.2 Add Components declaration
    top_file.write(to_comment(['Components declaration']))
    for _, cp in project.components.iteritems():
        top_file.write(cp.asEntity().asComponent())
        top_file.write("\n\n")
    
    # 2.3 Add Intercons declaration
    for cp in intercons:
        top_file.write(cp.asComponent)
        top_file.write("\n\n")

    # 2.4 Add Syscon declaration
    top_file.write(clk_ip.asComponent)
    top_file.write("\n\n")

    # 3. Building system
    top_file.write("\nbegin\n")
    
    # 3.1 Add IPs top modules
    for _, cp in project.instances.iteritems():
        top_file.write(str(cp))
        top_file.write("\n\n")

    # 3.2 Add intercons
    for cp in intercons:
        top_file.write(str(cp))
        top_file.write("\n\n")
        
    # 3.3 Add reset synchronization modules
    for name, _ in project.clocks.iteritems():
        clk_ip.setPort("clk", name)
        clk_ip.setPort("reset_sync", name + "_sync_reset")
        clk_ip.name = "syscon_" + name
        top_file.write(str(clk_ip))
        top_file.write("\n\n")
    
    top_file.write("\nend architecture;\n")
    top_file.close()
    
    entity = Entity(StringIO(entity))

    # 4 Saving settings into project
    project.port_list = entity_ports
    project.clock_list = entity_clocks
    project.hdl_files.extend(hdl_files)
    project.entity = Instance(entity)
