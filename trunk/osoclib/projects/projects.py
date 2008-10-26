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

# PROJECTS_NODES define Project XML file sections and attributs
PROJECTS_COMPONENTS_NODES = {
    "generics"      : ("name", "value"),
    "interfaces"    : ("name", "offset", "link")
}

PROJECTS_NODES = {
    "routes"        : ("name", "type"),
    "clocks"        : ("name", "frequency", "type"),
    "components"    : {"subnodes" : PROJECTS_COMPONENTS_NODES, "attribs" : ("name", "base") }
}

# PROJECTS_ATTRIBS define XML base node attributes
PROJECTS_ATTRIBS = {"name":"", "version":"", "author":"", "board" :""}

class ProjectError(Exception):
    """Exception raised when errors detected during project management.

    Attributs:
        message -- textual explanation of the error
    """

    __slots__ = ['message']

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class Project(XmlFileBase):
    """Projects managment class.

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
    
    def addComponent(self):
        pass
    
