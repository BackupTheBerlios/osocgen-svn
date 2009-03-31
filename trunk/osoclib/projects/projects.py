#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     protects.py
# Purpose:  Orchestra SoC projects manipulation routines
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/06/13
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

"Orchestra SoC projects manipulation routines"

__version__     = "1.0"
__versionTime__ = "13/06/2008"
__author__      = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import sys

if __name__ == "__main__":
    import os.path as path

    # Add base library to load path
    dirname, base = path.split(path.dirname(path.realpath(__file__)))
    sys.path.append(dirname)

from core import XmlFileBase
from components import find_component
from vhdl import make_top, TopError, make_testbench, TestbenchError
from vhdl import make_simulation

# PROJECTS_COMPONENTS_NODES define Project XML file sub-sections and attributes
# for component section.
PROJECTS_COMPONENTS_NODES = {
    "generics"      : ("name", "value"),
    "interfaces"    : ("name", "offset", "link")
}

# PROJECTS_NODED define Project XML file section and attributes
PROJECTS_NODES = {
    "wires"        : ("name", "type"),
    "clocks"        : ("name", "frequency", "type"),
    "components"    : {"subnodes" : PROJECTS_COMPONENTS_NODES, 
                       "attribs" : ("name", "base", "version") }
}

# PROJECTS_ATTRIBS define XML base node attributes
PROJECTS_ATTRIBS = {"name":"", "version":"", "author":"", "target" :""}

def need_cleanup(func):
    def do_cleanup(project, *args, **kwargs):
        project.clean_up()
        # pylint: disable-msg=W0142
        return func(project, *args, **kwargs)
    
    return do_cleanup
        
class ProjectError(Exception):
    """Exception raised when errors detected during project management.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class ProjectData(object):
    __slots__ = ("name", "path", "components", "wires", "clocks", "externals",
                 "instances", "port_list", "entity", "hdl_files", "soc",
                 "clock_list")
    
    def __init__(self, project, output_dir, hdl_files):
        self.name = project.name
        self.soc = project
        self.path = output_dir
        self.components = project._components
        self.wires = project._wires
        self.clocks = project._clocks
        self.externals = project._extern
        self.instances = project._instances
        self.hdl_files = hdl_files
        self.port_list = {}
        self.clock_list = {}
        self.entity = None

class Project(XmlFileBase):
    """Projects management class.

    Attributes:
        filename -- Name of file which describe the project
    """
    xml_basename = "project"
    _config = None
    _filename = None
    _components = {}
    _instances = {}
    _wires = {}
    _valid = False
    _errors = {}
    _clocks = {}
    _extern = []

    @property
    def filename(self):
        return self._filename

    @property
    def is_valid(self):
        """Return True if errors have been detected for this interface."""
        return self._valid
    
    @property
    def last_errors(self):
        """Return errors detected for this interface during last check."""
        return self._errors

    def clean_up(self):
        """Clear all checking results."""
        self._components = {}
        self._instances = {}
        self._wires = {}
        self._clocks = {}
        self._extern = []
        self._valid = False
        
    def __init__(self, filename=None):
        XmlFileBase.__init__(self, PROJECTS_NODES, PROJECTS_ATTRIBS, filename, 
                             None)
        
        if filename:
            self._filename = filename
             
        # Convert default string value into integer
        for clock in self.clocks.iteritems():
            clock.frequency = int(clock.frequency)

    def save(self, filename=None):
        """Save project to disk."""

        if filename:
            self._filename = filename
        
        if self._filename:
            fd = open(self._filename, "wb")
            fd.write(self.asXML())
            fd.close()

    @need_cleanup
    # pylint: disable-msg=W0622
    def addWire(self, name, type):
        """Add new bus to project
        
        Attributes
            name - bus name
            type - bus type (???)
        """

        name = str(name).lower()

        # Check if there is no clock domain with the same name
        for route in self.wires.iteritems():
            if route.name == name:
                raise ProjectError("*** Wire called '%s' already exist in current project, wire addition canceled.\n" % name)

        self.wires.add(name=name, type=type)
    
    @need_cleanup
    def removeWire(self, name):
        """Remove a bus from project
        
        Attributes
            name - the bus name
        """
        name = str(name).lower()
        if not self.wires.remove(name):
            raise ProjectError("*** No write called '%s' exist in current project, wire deletion canceled.\n" % name)
    
    
    @need_cleanup
    # pylint: disable-msg=W0622
    def addClock(self, name, frequency, type):
        """Add new clock domain to project
        
        Attributes
            name - clock domain name
            frequency - clock frequency in Hertz
            type - clock type (static or PLL)
        """

        name = str(name).lower()

        # Check if there is no clock domain with the same name
        for clock in self.clocks.iteritems():
            if clock.name == name:
                raise ProjectError("*** Clock domain called '%s' already exist in current project, clock addition canceled.\n" % name)

        self.clocks.add(name=name, frequency=frequency, type=type)

    @need_cleanup
    def removeClock(self, name):
        """Remove a clock domain from project
        
        Attributes
            name - the clock domain name
        """
        
        name = str(name).lower()
        clock = self.clocks.getElement(name)
        if not clock:
            raise ProjectError("*** No clock domain called '%s' exist in current project, clock deletion canceled.\n" % name)
        
        for cpnode in self.components:
            for ifacenode in cpnode[1]["interfaces"]:
                if ifacenode[0].link == name:
                    raise ProjectError("*** Clock '%s' used by instance '%s', clock deletion canceled.\n" % (name, cpnode[0].name))
                     
    @need_cleanup            
    def addComponent(self, name, component):
        """Add new component to project
        
        Attributes
            name - the component instance name
            component - the component to be added
        """

        name = str(name).lower()
        
        # Check if there is no component instance with the same name
        for cp in self.components.iteritems():
            if cp.name == name:
                raise ProjectError("*** Component called '%s' already exist in current project, component addition canceled.\n" % name)
    
        # Add component instance to current project and retrieve component details
        (_, properties) = self.components.add(name=name,
                                              base=component.name,
                                              version=component.version)

        # Add generic parameters to this instance
        for generic in component.generics.iteritems():
            properties["generics"].add(name=generic.name, value=generic.value)
            
        # Add interfaces to this instance
        for interface in component.interfaces.iteritems():
            properties["interfaces"].add(name=interface.name, offset="")
    
    @need_cleanup  
    def removeComponent(self, name):
        """Remove a component instance from project
        
        Attributes
            name - the component instance name
        """

        name = str(name).lower()
        
        if not self.components.remove(name):
            raise ProjectError("*** No component called '%s' exist in current project, component deletion canceled.\n" % name)

    @need_cleanup
    def findComponent(self, name):
        """Search component instance in project
        
        Attributes
            name - the component instance name
        """

        name = str(name).lower()
        return self.components.getElement(name)
    
    @need_cleanup
    def check(self, component_dir):
        """Verify project integrity.
        
        Attributes
            component_dir - Orchestra IP directory
        """
        
        # Clean all caches
        errors = {}
        self._valid = True

        # Verification steps
        # 1. clocks
        #      Verify that almost 1 clock is declared
        chk_errors = []
        if len(self.clocks):
            for clock in self.clocks.iteritems():
                if(clock.frequency == 0):
                    chk_errors.append("*** Clock '%s' has bad frequency value." % clock.name)
        else:
            chk_errors.append("*** No clock domain defined.")
            
        if chk_errors:
            errors["clocks"] = chk_errors 
            self._valid = False

        self._clocks = dict([clock.name.lower(), []] 
                                for clock in self.clocks.iteritems()
                           )

        # 2. Wires
        #      Verify that at least 1 wire is defined
        wire_errors = []
        self._wires = dict([wire.name.lower(), ([], [])] 
                                for wire in self.wires.iteritems()
                           )
        if not len(self._wires):
            wire_errors.append("*** No wire defined.")
        
        # 3. components
        # 3.1 Interfaces
        #       Verify that each clock interface is connected to a clock domain
        #       Verify that each master and slave interface is connected to a route
        #       Verify that each slave interface has a valid address
        #       Verify address overlapping
        # 3.2 Generics
        #       ??????
        chk_errors = []
        chk_warns = []
        for (cp, cp_attr) in self.components:
            if self._components.has_key(cp.base):
                cp_data = self._components[cp.base]
            else:
                # New component detected, try to load it
                cp_data = find_component(component_dir, cp.base)
                if not cp_data:
                    chk_errors.append("Component '%s' don't exist." % cp.base)
                    continue

                # Check it's validity
                if cp_data.has_errors:
                    errors[("IP %s" % cp.base)] = cp_data.last_errors
                    self._valid = False

                # Save it for future use
                self._components[cp.base] = cp_data
            
            # Add component instance to list
            generics = cp_attr["generics"].asDict("name","value")
            instance = cp_data.asInstance(name=cp.name, generics=generics)
            self._instances[cp.name] = instance
            
            # Verify instance integrity
            if instance.has_errors:
                errors[("Component %s" % cp.name)] = instance.last_errors
                self._valid = False
                
            # Convert base IP interfaces to dictionary
            cp_ifaces = dict([iface.name.lower(), [iface.type.upper(), False]]
                                for iface in cp_data.interfaces.iteritems()
                            )

            # Check interfaces settings
            for iface in cp_attr["interfaces"].iteritems():
                if cp_ifaces.has_key(iface.name.lower()):
                    cpiface = cp_ifaces[iface.name.lower()]
                    if cpiface[1]:
                        chk_errors.append("Component '%s', duplicate interface '%s' declaration." % (cp.name, iface.name))
                        
                    # Mark interface as used
                    cpiface[1] = True
                else:
                    chk_errors.append("Component '%s', interface '%s' not present in base IP '%s'." % (cp.name, iface.name, cp.base))
                    continue
                
                if cpiface[0] == "WBC":
                    if iface.offset:
                        chk_warns.append("Component '%s', clock interface '%s' unused parameter OFFSET." % (cp.name, iface.name))
                        
                    if not iface.link:
                        chk_errors.append("Component '%s', clock interface '%s' not connected." % (cp.name, iface.name))
                    elif not self.clocks.hasElement(iface.link):
                        chk_errors.append("Component '%s', clock interface '%s' connected to unavailable clock '%s'." % (cp.name, iface.name, iface.link))
                    else:
                        self._clocks[iface.link.lower()].append(instance.interface(iface.name.lower()))

                elif cpiface[0] == "WBM":
                    if iface.offset:
                        chk_warns.append("Component '%s', master interface '%s' unused parameter OFFSET." % (cp.name, iface.name))

                    if not iface.link:
                        chk_errors.append("Component '%s', master interface '%s' not connected." % (cp.name, iface.name))
                    elif not self.wires.hasElement(iface.link):
                        chk_errors.append("Component '%s', master interface '%s' connected to unavailable bus/wire '%s'." % (cp.name, iface.name, iface.link))
                    else:
                        wire = self._wires[iface.link.lower()]
                        wire[0].append(instance.interface(iface.name.lower()))

                elif cpiface[0] == "WBS":
                    # Store interface base address as instance settings.
                    instance.setOffset(iface.name, iface.offset)
                    if not iface.link:
                        chk_errors.append("Component '%s', slave interface '%s' not connected." % (cp.name, iface.name))
                    elif not self.wires.hasElement(iface.link):
                        chk_errors.append("Component '%s', slave interface '%s' connected to unavailable bus/wire '%s'." % (cp.name, iface.name, iface.link))
                    else:
                        wire = self._wires[iface.link.lower()]
                        wire[1].append(instance.interface(iface.name.lower()))

                elif cpiface[0] == "GLS":
                    self._extern.append(instance.interface(iface.name.lower()))
                else:
                    chk_errors.append("Component '%s', interface '%s' unknown type '%s'." % (cp.name, iface.name, cpiface[0]))

            # Verify interfaces settings
            for (ifname, ifparam) in cp_ifaces.iteritems():
                if not ifparam[1]:
                    if ifparam[0] == "GLS":
                        chk_warns.append("Component '%s', globals interface '%s' not used." % (cp.name, ifname))
                    elif ifparam[0] == "WBC":
                        chk_errors.append("Component '%s', clock interface '%s' not connected." % (cp.name, ifname))
                    elif ifparam[0] == "WBM":
                        chk_errors.append("Component '%s', master interface '%s' not connected." % (cp.name, ifname))
                    elif ifparam[0] == "WBS":
                        chk_errors.append("Component '%s', slave interface '%s' not connected." % (cp.name, ifname))
                    else:
                        chk_errors.append("Component '%s', interface '%s' not used." % (cp.name, ifname))
                            
        if not self.components:
            chk_errors.append("No components in project.")

        if chk_errors:
            self._valid = False
            chk = [(("ERR: %s") % e) for e in chk_errors]
            chk_errors = chk
        
        if chk_warns:
            chk = [(("WARN: %s") % w) for w in chk_warns]
            chk_errors.extend(chk)
            
        if chk_errors:
            errors["Components"] = chk_errors
            
        # 4. Verify that each wire has at least one master and one slave
        for w_name, w_iface in self._wires.iteritems():
            if len(w_iface[0]) == 0:
                wire_errors.append("Wire '%s' has no master." % w_name)
            if len(w_iface[1]) == 0:
                wire_errors.append("Wire '%s' has no slave." % w_name)
                
        if wire_errors:
            errors["Wire"] = wire_errors
            self._valid = False
            
        self._errors = errors
        return errors

    def compile(self, component_dir, output_dir):
        """Generate project output files.

        @param component_dir: Orchestra IP directory
        @param output_dir: Destination directory  
        @raise ProjectError: if any error detected during process 
        """
                
        # 1. Check design settings if not done before
        if len(self._components) == 0:
            self.check(component_dir)
            
        # 2. Only valid designs can be generated
        if self._valid == False:
            raise ProjectError("*** Project has errors, compilation canceled.\n")

        # 3. Extract HDL files
        file_names = []
        for _, cp in self._components.iteritems():
            file_names.extend(cp.extractHDL(output_dir))
        
        # 4. Create top module for system on chip
        project = ProjectData(self, output_dir, file_names)
        try:
            make_top(project)
        except TopError, e:
            raise ProjectError(e.message)
        
        # 4: Create compilation project
        
        # 5: Create simulation module
        try:
            tb_file = make_testbench(project)
        except TestbenchError, e:
            raise ProjectError(e.message)
        file_names.append(tb_file)
        make_simulation(project, file_names)
        