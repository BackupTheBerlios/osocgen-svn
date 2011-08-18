#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     targets.py
# Purpose:  Orchestra SoC targets manipulation routines
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/06/13
# License:  GPLv3 or newer
#=============================================================================
# Last commit info:
#
# $LastChangedDate:: xxxx/xx/xx xx:xx:xx $
# $Rev::                                 $
# $Author::                              $
#=============================================================================
# Revision list :
#
# Date       By        Changes
#
#=============================================================================

"Orchestra SoC targets manipulation routines"

__version__     = "1.0"
__versionTime__ = "19/04/2009"
__author__      = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import sys

if __name__ == "__main__":
    import os.path as path

    # Add base library to load path
    dirname, _ = path.split(path.dirname(path.realpath(__file__)))
    sys.path.append(dirname)

from core import XmlFileBase

# TARGETS_IPS_NODES define Target XML file sub-sections and attributes for IP
# section.
TARGETS_IPS_NODES = {
    "generics"      : ("name", "value"),
    "interfaces"    : ("name", "offset", "link"),
    "pads"          : ("name", "loc", "options")
}

# TARGETS_MODULES_NODES define Target XML file sub-sections and attributes for
# module section.
TARGETS_MODULES_NODES = {
    "pads"      : ("name", "loc", "options")
}

# PROJECTS_NODED define Project XML file section and attributes
TARGETS_NODES = {
    "clocks"    : ("name", "freq", "loc"),
    "modules"   : {"subnodes": TARGETS_MODULES_NODES,
                   "attribs": ("name", "options")},
    "ips"       : {"subnodes" : TARGETS_IPS_NODES, 
                   "attribs" : ("name", "base", "version") }
}

# PROJECTS_ATTRIBS define XML base node attributes
TARGETS_ATTRIBS = {"name":"", "version":"", "author":"", "vendor":"", 
                   "family":"", "package":"", "speed":"", "device":""
}

class TargetError(Exception):
    """Exception raised when errors detected during target management.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class Target(XmlFileBase):
    """Targets management class.

    Attributes:
        filename -- Name of file which describe the project
    """
    xml_basename = "target"

    def __init__(self, filename=None):
        XmlFileBase.__init__(self, TARGETS_NODES, TARGETS_ATTRIBS, filename, 
                             None)
        
        if filename:
            self._filename = filename
             
        # Convert default string value into integer
        for clock in self.clocks.iteritems():
            clock.frequency = int(clock.frequency)

    def save(self, filename=None):
        """Save target to disk."""

        if filename:
            self._filename = filename
        
        if self._filename:
            fd = open(self._filename, "wb")
            fd.write(self.asXML())
            fd.close()
