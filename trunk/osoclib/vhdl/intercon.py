#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     intercon.py
# Purpose:  VHDL tools for Orchestra
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/12/15
# License:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

"""This script will be able to generate intercon module for an Orchestra system.
"""

__version__ = "$Id$"
__versionTime__ = "15/12/2008"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"
__license__ = "GPLv3"
__copyright__ = "Copyright 2008 Fabrice MOUSSET"

import os.path as path
from StringIO import StringIO
from entity import Entity, Instance
from utils import make_header, _VHDL_ARCHITECTURE, to_bit_vector
from utils import to_comment, signal_name, port_declaration

def mk_signal_bit(name, idx):
    if name == 1:
        return None
    if not idx is None:
        return ("%s(%d)" % (name, idx))
    
    return str(name)

def mk_signal(c_name, c_idx, l_idx, idx, c_start_idx):
    signal = ""
    if c_name == 1:
        if c_start_idx == idx-1:
            signal = "'1'"
        else:
            signal = ('"%s"' % ('1'*(idx-c_start_idx)))
    elif c_idx:
        if c_start_idx == idx-1:
            signal = ("%s(%d)" % (c_name, c_idx))
        else:
            signal = ("%s(%d downto %d)" % (c_name, l_idx, c_idx))
    else:
        signal = str(c_name)
        
    return signal

def mk_signal_vector(bus, start, end):
    """Generate signal vector from a signal list.
    
        @param bus: list of signal (signal_name, signal_idx)
        @param start: vector start index
        @param end: vector end index
        @return: VHDL signal vector or signal  
    """
    c_name, c_idx = bus[start]
    if start == end:
        if c_name == 1:
            return "'1'"
        if c_idx:
            return "%s(%d)" % (c_name, c_idx)
        return str(c_name)
    
    signals = []
    c_start_idx = start
    s_idx = c_idx
    for idx in range(start, end):
        l_idx = s_idx
        s_name, s_idx = bus[idx]
        if str(s_name) != str(c_name):
            signals.append(mk_signal(c_name, c_idx, l_idx, idx, c_start_idx))
            c_name, c_idx = s_name, s_idx

    idx = end
    signals.append(mk_signal(c_name, c_idx, l_idx, idx, c_start_idx))
    
    return "&".join(signals.reverse())

def mk_sel_bit(master, idx, sel_width, byte_width):
    """Creation byte selection bits for a specific master interface.
    
        @param master: Master interface
        @param idx: Byte selection bit index
        @param sel_width: Master byte selection bus real width
        @param byte_width: Master byte selection bus theoretical width.
    """
    if sel_width == 0:
        return None
    elif sel_width == 1:
        return signal_name(master, "sel_i")
    elif sel_width == byte_width:
        return mk_signal_bit(signal_name(master, "sel_i"), idx)
    else:
        idx2 =  byte_width // sel_width
        return mk_signal_bit(signal_name(master, "sel_i"), idx//idx2)

def mk_sel_comb(addr_name, master_sel, addr_bit, idx):
    def _to_signal(idx, bit_cpt, addr_name):
        if (idx & (2**bit_cpt)) == 0:
            return "not(%s(%d))" % (addr_name, bit_cpt)
        else:
            return "%s(%d)" % (addr_name, bit_cpt)
    
    name = master_sel[idx%len(master_sel)]
    idx //= len(master_sel)
    names = [_to_signal(idx, bit_cpt, addr_name) 
                    for bit_cpt in range(addr_bit)
            ]

    if name != None:
        names.insert(0, name)

    return " and ".join(names)

def mk_sel_array(master, master_sel, slave_bytes):
    """Creation byte selection bits for a specific master interface.
    
        @param master: Master interface
        @param master_sel: Byte selection bit index
        @param slave_bytes: Slave byte selection bus width
    """
    if slave_bytes > len(master_sel):
        bit_pow = slave_bytes / len(master_sel)
        bit_cpt = 0
        while 2**bit_cpt < bit_pow:
            bit_cpt += 1
        
        name = signal_name(master, "adr_i")
        return (bit_cpt, [mk_sel_comb(name, master_sel, bit_cpt, idx) 
                                for idx in range(slave_bytes)
                ])
    else:
        return (0, [master_sel[idx] for idx in range(slave_bytes)])

class InterconError(Exception):
    """Exception raised when errors detected during Intercon manipulation.

    Attributes:
        message -- textual explanation of the error
    """

    __slots__ = ('message')

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message

class InterconRegisterIface(object):
    """
    Help class to manage intercon interfaces parameters
    """
    def __init__(self, slave, master, sel, sels):
        self.master = master
        self.slave = slave
        self.sel = sel
        self.sels = sels

        # Get slave address bus width in bytes
        self.slave_byte_sel = slave.data_width // 8

        # Get addr signals used for sel signals coding
        for idx in range(len(sels)):
            if 2**idx == self.slave_byte_sel:
                self.sel_base, _ = self.sels[idx]
        
        # Get master address bus width in bytes
        self.master_byte_sel = master.data_width // 8
        
        # Compute slave address decoding settings
        self.addr_low = self.sel_base + slave.addr_width
        self.base_addr = slave.offset // (2**self.addr_low) 
        self.base_addr //= self.master_byte_sel
    
    @property
    def addr_sel(self):
        """Get interface base address based on master interface settings
        and slave interface settings.
        """
        width = self.master.addr_width - self.addr_low
        return '%s <= \'1\' when (%s(%d downto %d) = "%s") else \'0\'' % (
                                          self.sel,
                                          "wbs_master_adr_i",
                                          self.master.addr_width-1,
                                          self.addr_low,
                                          to_bit_vector(self.base_addr, width))

    @property
    def byte_ok(self):
        """Verify bytes selection array validity."""
        
        (sel_width, _) = self.slave.wb_signal_width("SEL")
        return sel_width != 0
            
    @property
    def byte_sel(self):
        """Get selection bits array for this slave."""

        def to_vector(name, start, length):
            vector = ["%s(%d)" % (name, start-idx) for idx in range(length)]
            return "(%s)" % " or ".join(vector)
        
        (sel_width, _) = self.slave.wb_signal_width("SEL")
        if sel_width == 0:
            return None
        
        sel_null = "'0'"
        if sel_width > 1:
            sel_null = "(others => '0')"
        
        name = signal_name(self.slave, "sel_o")
        sel_name = "master_sel%d" % (8*(2**(self.slave_byte_sel-1)))
        if sel_width < self.slave_byte_sel:
            step = self.slave_byte_sel//sel_width
            sel = "&".join([to_vector(sel_name, idx-1, step) 
                                for idx in range(self.slave_byte_sel, 0, -step)
                            ])
        else:    
            sel = sel_name
        
        return ("%s <= %s when (%s = '1') else %s" % (name, sel, self.sel,
                                                     sel_null)) 
    
    @property
    def ack(self):
        """Get acknowledge signals for this slave."""

        name = "'1'"
        if self.slave.has_signal("ACK"):
            name = signal_name(self.slave, "ack_i")

        return ("%s when (%s = '1')" % (name, self.sel)) 

    @property
    def control(self):
        """Get control signals for this slave."""

        return [("%s <= %s when %s = '1' else '0'" % 
                    (signal_name(self.slave, sig_type+"_o"), 
                     ("wbs_master_%s_i"%sig_type), self.sel))
                        for sig_type in ["cyc", "we", "stb"]
                  ]

    @property    
    def addr(self):
        """Get slave interface address bus.
        """
        addr_width = self.slave.addr_width
        addr_null = "'0'"
        addr = "wbs_master_adr_i"
        if addr_width > 1:
            addr_null = "(others => '0')"
            addr = "%s(%d downto %d)" % (addr, self.addr_low-1, self.sel_base)
        else:
            addr = "%s(%d)" % (addr, self.addr_low-1)

        name = signal_name(self.slave, "adr_o")
        return ("%s <= %s when (%s = '1') else %s" % (name, addr, self.sel, 
                                                       addr_null)) 

    @property
    def writedata_ok(self):
        """Verify writedata bus validity."""
        (s_dat_width, _) = self.slave.wb_signal_width("DAT")
        return s_dat_width != 0

    @property    
    def writedata(self):
        """Generate slave data bus output signals.
        """
        (_, m_dat_width) = self.master.wb_signal_width("DAT")
        (s_dat_width, _) = self.slave.wb_signal_width("DAT")

        if s_dat_width == 0:
            return None

        s_name = signal_name(self.slave, "dat_o")
        m_name = "wbs_master_dat_i"
        dat_nul = "(others => '0')"

        if s_dat_width > m_dat_width:
            m_name = "&".join([m_name] * (s_dat_width // m_dat_width))
        elif s_dat_width < m_dat_width:
            m_name = ("%s(%d downto 0)" % (m_name, s_dat_width-1))
        
        return ("%s <= %s when (%s = '1') else %s" % 
                (s_name, m_name, self.sel, dat_nul))

    def readdata_ok(self, byte):
        """Verify readdata bus validity."""
        (m_dat_width, _) = self.master.wb_signal_width("DAT")
        (_, s_dat_width) = self.slave.wb_signal_width("DAT")
        return (s_dat_width != 0 and m_dat_width != 0 and 
                byte < self.slave_byte_sel) 

    def readdata(self, byte):
        """Generate slave data bus input signals.
        """
        (m_dat_width, _) = self.master.wb_signal_width("DAT")
        (_, s_dat_width) = self.slave.wb_signal_width("DAT")

        if m_dat_width == 0 or s_dat_width == 0 or self.slave_byte_sel <= byte:
            return None

        s_name = signal_name(self.slave, "dat_i")
        sel = "master_sel%d" % (8*(2**(self.slave_byte_sel-1)))
        if self.slave_byte_sel == 1:
            return [("%s when (%s='1' and %s='1')" % (s_name, self.sel, sel))]
    
        return ["%s(%u downto %u) when (%s='1' and %s(%d)='1')" % 
                (s_name, idx*8+7, idx*8, self.sel, sel, idx)
                    for idx in range(byte, self.slave_byte_sel, 
                                     self.master_byte_sel)
                ]

class InterconMemoryIface(InterconRegisterIface):
    pass

def port_matrix(iface, signal, defname = None):
    """Generate port signal settings.
    """
    port_name, port_type = port_declaration(iface, signal, defname)
    port_cnx = iface.getPortCnx(signal[0].name)
    return (port_name, [port_type, port_cnx])

def make_intercon(name, base_dir, master, slaves):
    """Intercon module generation.
    
    The intercon module is used to generate all the necessary logic glue to
    allow master interface to communicate with each slave.
    
        @param name: intercon module name
        @param base_dir: destination directory
        @param masters: master interfaces signals
        @param slaves: slave interfaces signals
        @return: vhdl.Entity instance from Intercom module.
        
        master[0] = InstanceInterface object
        master[1] = {'signal_name' : 'signal attached'}
    """
    base_name = ("intercon_%s" % name)
    filename = path.join(base_dir, ("%s.vhd" % base_name))

    # Generate master bytes selection signals list
    _, sel_width = master.wb_signal_width("SEL")
    byte_width = master.data_width // 8

    master_sel = [ mk_sel_bit(master, idx, sel_width, byte_width)
                    for idx in range(byte_width)
                 ]
    
    try:
        vhdl_fd = open(filename, "w")
    except IOError:
        raise InterconError("Can't create %s.vhd file." % base_name)

    vhdl_fd.write(make_header("Wishbone address decoder module", base_name))
    
    # 1. Building Entity declaration
    entity = "entity %s is\n" % base_name
    entity += "  port (\n"
    #entity += "    -- Global signals\n"
    #entity += "    clk : in std_logic;\n"
    #entity += "    reset : in std_logic;\n\n"
    
    entity += "    -- Master signals\n"
    
    # for signal in master.
    entity_ports =  dict(port_matrix(master, signal, "wbs_master") 
                            for _, signal in master.signals.iteritems()
                            )
    ports = ["    %s : %s" % (key, value[0]) 
                for key, value in entity_ports.iteritems()
            ]
    entity += ";\n".join(ports)

    slaves_max_width = 8
    for slave in slaves:
        entity += ";\n\n    -- Slave %s.%s signals\n" % (slave.instance_name,
                                                         slave.name)
        
        if slave.data_width > slaves_max_width:
            slaves_max_width = slave.data_width 
        # for signal out slave.

        slave_ports =  dict(port_matrix(slave, signal) 
                                for _, signal in slave.signals.iteritems()
                                )
        entity_ports.update(slave_ports)
        entity += ";\n".join(["    %s : %s" % (key, value[0]) 
                              for key, value in slave_ports.iteritems()
                              ])

    entity += "\n  );"
    entity += "\nend entity;\n"

    vhdl_fd.write(entity)

    # 2. Starting Architecture declaration
    vhdl_fd.write(_VHDL_ARCHITECTURE % (base_name))

    slaves_max_width //= 8
    slaves_max_sel = 0
    while 2**slaves_max_sel < slaves_max_width:
        slaves_max_sel += 1
    
    master_sels = [mk_sel_array(master, master_sel, 2**idx) 
                        for idx in range(slaves_max_sel+1)]
    
    if(len(slaves) > 1):
        slave_cnx = [InterconRegisterIface(slave, master, 
                                           "slave_sel(%d)"%idx,
                                           master_sels)
                        for idx, slave in enumerate(slaves)
                    ]
    else:
        slave_cnx = [InterconRegisterIface(slaves[0], master, 
                                           "slave_sel",
                                           master_sels)
                    ]

    # 3. Adding local signals
    vhdl_fd.write(to_comment(['Signals declaration']))
    if(len(slaves) > 1):
        vhdl_fd.write("  signal slave_sel : std_logic_vector(%u downto 0);\n" % 
                      (len(slaves) - 1))
    else:
        vhdl_fd.write("  signal slave_sel : std_logic;\n") 

    # 3.1 Adding bytes selection signals
    for idx, sels in enumerate(master_sels):
        (_, signals) = sels
        if len(signals) == 1:
            vhdl_fd.write("  signal master_sel%u : std_logic;\n" % (8 * (2 ** idx)))
        else:
            vhdl_fd.write("  signal master_sel%u : std_logic_vector(%d downto 0);\n" % 
                          (8 * (2 ** idx),  len(signals) - 1))
    
    vhdl_fd.write("\nbegin\n")
     
    # 4. Building address decoders
    vhdl_fd.write(to_comment(['Byte selection signals']))
    for idx, sels in enumerate(master_sels):
        def _to_signal(sig):
            if sig == None:
                return "'1'"
            else:
                return sig
            
        (_, signals) = sels
        if len(signals) == 1:
            vhdl_fd.write("  master_sel%u <= %s;\n" % 
                          (8 * (2 ** idx), _to_signal(signals[0])))
        else:
            vhdl = ["  master_sel%u(%u) <= %s;\n" % 
                          (8 * (2 ** idx), idx2, _to_signal(signals[idx2]))
                          for idx2 in range(len(signals))]
            vhdl_fd.write("".join(vhdl))

    # 4. Building address decoders
    vhdl_fd.write(to_comment(['Address decoders']))
    vhdl = [slave.addr_sel for slave in slave_cnx]
    vhdl_fd.write("  %s;\n" % ";\n  ".join(vhdl))

    vhdl = [slave.addr for slave in slave_cnx]
    vhdl_fd.write("  %s;\n" % ";\n  ".join(vhdl))
    
    # 5. Building acknowledge signal
    vhdl_fd.write(to_comment(['Control signals']))
    vhdl = [slave.ack for slave in slave_cnx]
    vhdl.append("'0'")
    vhdl_fd.write("  wbs_master_ack_o <= %s;\n" % 
                  "\n                      else ".join(vhdl))

    vhdl = ["  %s;\n" % ";\n  ".join(slave.control) for slave in slave_cnx]
    vhdl_fd.write("\n".join(vhdl))
    
    # 6. Building datapath
    vhdl_fd.write(to_comment(['Datapath wrapping']))
    vhdl = [slave.byte_sel for slave in slave_cnx if slave.byte_ok]
    if len(vhdl):
        vhdl_fd.write("  %s;\n" % ";\n  ".join(vhdl))

    vhdl = [slave.writedata for slave in slave_cnx if slave.writedata_ok]
    if len(vhdl):
        vhdl_fd.write("  %s;\n" % ";\n  ".join(vhdl))

    if master.has_signal("dat", True):
        for idx in range(byte_width):
            vhdl = [slave.readdata(idx) for slave in slave_cnx 
                                            if slave.readdata_ok(idx)
                    ]
            vhdl = [elmt for elmt in reduce(list.__add__, vhdl) if elmt != None]
            name = "wbs_master_dat_o(%d downto %d)" % ((idx*8)+7, idx*8)
            if len(vhdl) == 0:
                vhdl_fd.write("  %s <= (others => '0');\n" % name)
            else:
                vhdl.append("(others => '0')")
                sep = "\n%s else " % (" " * (len(name) + 5))
                vhdl_fd.write("  %s <= %s;\n" % 
                              (name, sep.join(vhdl)))

    # 7. Closing module
    vhdl_fd.write("\nend architecture;\n")
    vhdl_fd.close()
    
    # 8. Create vhdl.Entity object
    entity = Entity(StringIO(entity))
    instance = Instance(entity, "CP_" + base_name)
    
    # 9. Adding signals interconnection
    ports = dict((key, value[1]) 
                 for key, value in entity_ports.iteritems())

    instance.setPorts(ports)

    # 10. Returning instance
    return instance, base_name+".vhd"
