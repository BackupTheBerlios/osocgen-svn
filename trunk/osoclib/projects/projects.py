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

__doc__         = "Orchestra SoC projects manipulation routines"
__version__     = "1.0"
__versionTime__ = "13/06/2008"
__author__      = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os, sys
import os.path as dir

if __name__ == "__main__":
    # Add base library to load path
    dirname, base = dir.split(dir.dirname(dir.realpath(__file__)))
    sys.path.append(dirname)

from core import XmlFileBase
from vhdl import Entity
from StringIO import StringIO
import string

# PROJECTS_COMPONENTS_NODES define Project XML file sub-sections and attributes
# for component section.
PROJECTS_COMPONENTS_NODES = {
    "generics"      : ("name", "value"),
    "interfaces"    : ("name", "offset", "link")
}

# PROJECTS_NODED define Project XML file section and attributes
PROJECTS_NODES = {
    "routes"        : ("name", "type"),
    "clocks"        : ("name", "frequency", "type"),
    "components"    : {"subnodes" : PROJECTS_COMPONENTS_NODES, "attribs" : ("name", "base", "version") }
}

# PROJECTS_ATTRIBS define XML base node attributes
PROJECTS_ATTRIBS = {"name":"", "version":"", "author":"", "board" :""}

class ProjectError(Exception):
    """Exception raised when errors detected during project management.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ['message']

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class Project(XmlFileBase):
    """Projects management class.

    Attributes:
        filename -- Name of file which describe the project
    """
    xml_basename = "project"
    filename = None

    def __init__(self, filename=None):
        XmlFileBase.__init__(self, PROJECTS_NODES, PROJECTS_ATTRIBS, filename, None)
        if filename:
            self.filename = filename

    def save(self, filename=None):
        """Save project to disk."""

        # Save to disk if file name specified
        if filename:
            file = open(filename, "wb")
            file.write(self.asXML())
            file.close()

    def addRoute(self, name, type):
        pass
    
    def addClock(self, name, frequency, type):
        pass
    
    def addComponent(self, name, component):
        """Add new component to current project
        
        Attributes
            name - the component instance name
            component - the component to be added
        """
        
        # Check if there is no component instance with the same name
        for cp in self.components:
            if cp.name == name:
                raise ProjectError("*** Component called '%s' already exist in current project, component addition canceled.\n" % name)
    
        # Add component instance to current project and retrieve component details
        (instance, properties) = self.components.add(None, name = name, base = component.name, version = component.version)

        # Add generic parameters to this instance
        for generic in component.generics:
            properties["generics"].add(None, name=generic.name, value=generic.value)
            
        # Add interfaces to this instance
        for interface in component.interfaces:
            properties["interfaces"].add(None, name=interface.name, offset="")
        