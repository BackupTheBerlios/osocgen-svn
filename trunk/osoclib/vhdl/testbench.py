#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     simuli.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2000/02/04
# License:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

"""This script will be able to generate simulation module for an Ochestra system.
"""
__version__ = "$Id$"
__versionTime__ = "23/03/2009"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2009 Fabrice MOUSSET"

import os.path as path
from utils import make_header, _VHDL_ARCHITECTURE, to_comment

class TestbenchError(Exception):
    """Exception raised when errors detected during test bench creation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

def make_simulation(project, hdl_files):
    """Create simulation project for ModelSim

        @param project: System on Chip project settings
        @param hdl_files: HDL files used by project 
    """
    base_name = ("%s.do" % project.name)
    filename = path.join(project.path, base_name)

    try:
        simu_fd = open(filename, "w")
    except IOError:
        raise TestbenchError("Can't create %s file." % base_name)

    simu_fd.write("vlib WORK\n\n")
    files = ["vcom -93 %s\n" % name for name in hdl_files]
    simu_fd.write("".join(files))
    simu_fd.write("\nvsim %s_tb\n" % project.name)
    simu_fd.close()
    
def make_testbench(project):
    """Testbench module generation.
    
    The testbench module is used to generate all the necessary code to
    create a instance of System on Chip and to start simulation.
    
        @param project: System on Chip project settings 
    """
    base_name = ("%s_tb" % project.name)
    project.entity.name = base_name
    filename = path.join(project.path, ("%s.vhd" % base_name))

    try:
        vhdl_fd = open(filename, "w")
    except IOError:
        raise TestbenchError("Can't create %s.vhd file." % base_name)

    vhdl_fd.write(make_header("System on Chip testbench skeleton.", 
                                base_name))
    
    # 1. Building Entity declaration
    vhdl_fd.write("entity %s is\nend entity;\n" % base_name)

    # 2. Starting Architecture declaration
    vhdl_fd.write(_VHDL_ARCHITECTURE % (base_name))

    # 3. Adding project constants
    vhdl_fd.write(to_comment(['Project constants']))
    reset_min = 0
    const_def = []
    for clk in project.soc.clocks.iteritems():
        const_def.append("  constant %s_PERIOD : time := 1 sec / %d;" % 
                          (clk.name.upper(), clk.frequency))
        if clk.frequency < reset_min or reset_min == 0:
            reset_min = clk.frequency
            
    const_def.append("  constant RESET_ON : time := 1 sec / %d;" % 
                     (reset_min * 3))
    const_def.append("  constant RESET_OFF : time := RESET_ON * 5;")
    vhdl_fd.write("\n".join(const_def))
    vhdl_fd.write("\n")
    
    # 4. Adding local signals
    vhdl_fd.write(to_comment(['Signals declaration']))
    vhdl_fd.write("  signal reset : std_logic;\n")
    vhdl_fd.write("".join(["  signal %s : %s := '0';\n" % (name, sig_type)
                           for name, sig_type in project.clock_list.iteritems()
                           ]))
    vhdl_fd.write("".join(["  signal %s : %s;\n" % (name, sig_type)
                            for name, sig_type in project.port_list.iteritems()
                            ]))

    # 4.1. Connecting signals to Top entity
    project.entity.setPorts(dict((name, name) 
                                 for name in project.port_list.iterkeys()))
    
    project.entity.setPorts(dict((name, name) 
                                 for name in project.clock_list.iterkeys()))
    project.entity.setPorts({"reset":"reset"}) 

    # 5. Adding entity declaration
    vhdl_fd.write(to_comment(['Components declaration']))
    vhdl_fd.write(project.entity.asComponent)

    vhdl_fd.write("\n\nbegin\n")
    
    # 6. Adding clocks and reset signals
    vhdl_fd.write("  reset <= '0', '1' after RESET_ON, '0' after RESET_OFF;\n")
    vhdl_fd.write("".join(["  %s <= not %s after %s_PERIOD/2;\n" % 
                           (name, name, name)
                            for name in project.clock_list.keys()
                            ]))
    
    # 7. Adding SoC Top entity
    vhdl_fd.write(str(project.entity))
    
    # 8. Closing module
    vhdl_fd.write("end architecture;\n")
    vhdl_fd.close()
    
    # 9. Returning file name
    return ("%s.vhd" % base_name)
