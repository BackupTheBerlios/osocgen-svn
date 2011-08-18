#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     syscon.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/12/15
# License:  GPLv3 or newer
#=============================================================================
# Revision list :
#
# Date       By        Changes
#
#=============================================================================

"""This script will be able to generate syscon module for an Orchestra system.

Syscon module is used to generate synchronous RESET signal for a given clock
domain.
"""
__version__ = "$Id$"
__versionTime__ = "15/12/2008"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2008 Fabrice MOUSSET"


__SYSCON_VHDL = """
-------------------------------------------------------------------------------
--  Design        : Wishbone Clock and Synchronous RESET generator.
--  File          : syscon.vhd
--  Related files : (none)
--  Author(s)     : Fabrice Mousset (fabrice.mousset@laposte.net)
-------------------------------------------------------------------------------
-- Released under both BSD license (see bsd.txt) and LGPL license (see lgpl.txt).
-- Whenever there is any discrepancy between the two licenses, the BSD license
-- will take precedence.
-------------------------------------------------------------------------------

library IEEE;
  use IEEE.std_logic_1164.all;
  use IEEE.numeric_std.all;

-- ----------------------------------------------------------------------------
--  Entity declaration
-- ----------------------------------------------------------------------------
Entity syscon is
  port
  (
    -- WISHBONE Interface
    clk        : in  std_logic;
    reset_sync : out std_logic;

    -- NON-WISHBONE Signals
    reset_ext  : in  std_logic
  );
End Entity;

-- ----------------------------------------------------------------------------
--  Architecture declaration
-- ----------------------------------------------------------------------------
Architecture RTL of syscon is

  signal delay: std_logic;
  signal reset: std_logic;

begin

  reset_sync <= reset;

  -- ---------------------------------------------------------------------------
  --  RESET signal generator process.
  -- ---------------------------------------------------------------------------
  process(clk)
  begin
    if(rising_edge(clk)) then
      delay <= ( not(reset_ext) and     delay  and not(reset) )
            or ( not(reset_ext) and not(delay) and     reset  );

      reset <= ( not(reset_ext) and not(delay) and not(reset) );
    end if;
  end process;

end architecture;
"""

import os.path as path
from StringIO import StringIO
from entity import Entity

class SysconError(Exception):
    """Exception raised when errors detected during Syscon manipulation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class SysconInstance(object):
    __slots__ = ("name", "ports", "generics")
    def __init__(self, name, ports):
        self.name = name
        self.ports = ports
        self.generics = None

def make_syscon(base_dir):
    """Create a Syscon VHDL module in specified directory.
    
    @param base_dir: destination directory.
    @return: vhdl.Entity instance from syscon definition. 
    """
    hdl = StringIO(__SYSCON_VHDL)
    try:
        vhdl_file = open(path.join(base_dir, "syscon.vhd"), "w")
    except IOError:
        raise SysconError("Can't create %s file." % 
                          path.join(base_dir, "syscon.vhd"))
    vhdl_file.write(hdl.getvalue())
    vhdl_file.close()

    return Entity(hdl), "syscon.vhd"
