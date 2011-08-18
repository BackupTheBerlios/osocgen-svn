#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     arbiter.py
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

"""This script will be able to generate an arbiter module for an Ochestra system.
"""
__version__ = "$Id$"
__versionTime__ = "04/02/2009"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2008 Fabrice MOUSSET"

__SYSCON_VHDL = """
-------------------------------------------------------------------------------
--  Design        : Round Robin arbiter module.
--  File          : rrarbiter.vhd
--  Related files : (none)
--  Author(s)     :  Benjamin Krill <ben@codiert.org>
--                   Fabrice Mousset <fabrice.mousset@laposte.net>
-------------------------------------------------------------------------------
-- Released under both BSD license (see bsd.txt) and LGPL license (see lgpl.txt).
-- Whenever there is any discrepancy between the two licenses, the BSD license
-- will take precedence.
-------------------------------------------------------------------------------

library ieee;
    use ieee.std_logic_1164.all;
    use IEEE.STD_Logic_unsigned.all;
    use IEEE.numeric_std.all;

-- ----------------------------------------------------------------------------
--  Entity declaration
-- ----------------------------------------------------------------------------
entity rrarbiter is
    generic ( 
        CNT : integer := 7 
    );
    port (
        -- WISHBONE Interface
        clk    : in    std_logic;
        rst    : in    std_logic;

        req    : in    std_logic_vector(CNT-1 downto 0);
        ack    : in    std_logic;
        grant  : out   std_logic_vector(CNT-1 downto 0)
    );
end;

-- ----------------------------------------------------------------------------
--  Architecture declaration
-- ----------------------------------------------------------------------------
architecture RTL of rrarbiter is
    signal grant_q : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal pre_req : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal gnt1    : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal gnt     : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal win     : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal req1    : std_logic_vector(CNT-1 downto 0) := (others => '0');
    signal ack_q   : std_logic := '0';
begin
    -- Make grant signal available
    grant <= grant_q;
    
    -- Mask off previous winners
    req1  <= req and not ((pre_req - 1) or pre_req);
    
    -- Select new winner
    gnt1  <= req1 and not(req1)+1;
    
    -- Isolate least significant set bit.
    gnt   <= req and not(req)+1;
    
    -- New winner selection
    win   <= gnt1 when (req1 /= 0) else gnt;

    -- -------------------------------------------------------------------------
    --  RESET signal generator process.
    -- -------------------------------------------------------------------------
    process (clk,rst)
    begin
    if rising_edge(clk) then
        if rst = '1' then
            pre_req <= (others => '0');
            grant_q <= (others => '0');
            ack_q   <= '0';
        else
            ack_q <= ack;
            if (ack = '1' or grant_q = 0) then
                pre_req <= win;
            end if;
    
            if grant_q = 0 or ack = '1' then
                grant_q <= win;
            end if;
        end if;
    end if;
    end process;

end architecture;
"""

import os.path as path
from StringIO import StringIO
from entity import Entity, Instance
from utils import make_header, _VHDL_ARCHITECTURE, to_bit_vector
from utils import to_comment, signal_name, port_declaration


class ArbiterError(Exception):
    """Exception raised when errors detected during Arbiter manipulation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

def make_arbiter(name, base_dir, masters, slave=None):
    """Arbiter module generation.
    
    The arbiter module is used to generate all the necessary logic glue to
    allow multi-masters to got access to a bus or a slave.
    
        @param name: arbiter module name
        @param base_dir: destination directory
        @param masters: master interfaces signals
        @param slave: slave interface signals
        @return: vhdl.Entity instance from Arbiter module.
        
        master[0] = InstanceInterface object
        master[1] = {'signal_name' : 'signal attached'}
    """
    base_name = ("arbiter_%s" % name)
    filename = path.join(base_dir, ("%s.vhd" % base_name))

    try:
        vhdl_fd = open(filename, "w")
    except IOError:
        raise ArbiterError("Can't create %s.vhd file." % base_name)

    vhdl_fd.write(make_header("Wishbone Round-Robin arbiter module", 
                                base_name))
    
    # 1. Building Entity declaration
    entity = "entity %s is\n" % base_name
    entity += "  port (\n"
    entity += "    -- Global signals\n"
    entity += "    clk : in std_logic;\n"
    entity += "    reset : in std_logic;\n\n"
    

    entity += "\n  );"
    entity += "\nend entity;\n"

    vhdl_fd.write(entity)

    # 2. Starting Architecture declaration
    vhdl_fd.write(_VHDL_ARCHITECTURE % (base_name))

    # 3. Adding local signals
    vhdl_fd.write(to_comment(['Signals declaration']))
    
    vhdl_fd.write("begin\n")
     
    
    # 7. Closing module
    vhdl_fd.write("end architecture;\n")
    vhdl_fd.close()
    
    # 8. Create vhdl.Entity object
    entity = Entity(StringIO(entity))
    instance = Instance(entity, base_name)
    
    # 9. Adding signals interconnection
    
    # 10. Returning instance
    return instance, ("%s.vhd" % base_name)
