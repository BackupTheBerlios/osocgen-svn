#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     wishbone.py
# Purpose:  Whisbone bus manipulation routines and constants
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/12/14
# Licence:  GPLv3 or newer
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

"Wishbone SoC signals declaration"

__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

# WB_SIGNALS define wishbone signals aliases
WB_SIGNALS = {
    "RST" : "RST", "RESET" : "RST",
    "CLK" : "CLK", "CLOCK" : "CLK",
    "ADR" : "ADR", "ADDR"  : "ADR", "ADDRESS"  : "ADR",
    "DAT" : "DAT", "DATA"  : "DAT", "READDATA" : "DAT", "WRITEDATA" : "DAT",
    "WE"  : "WE",  "WRITE" : "WE",
    "SEL" : "SEL", "SELECT": "SEL",
    "ACK" : "ACK",
    "CYC" : "CYC", "CYCLE" : "CYC",
    "STB" : "STB", "STROBE" : "STB"
}

# WB_SIGNALS define wishbone interfaces type and corresponding signal with direction
WB_INTERFACES = {
    "GLS" : ("Non Wishbone signals", {}),
    "WBM" : ("Wishbone Master",
             {"ADR":"O", "DAT":"IO", "WE":"O", "SEL":"o", "ACK":"I", "CYC":"O",
              "STB":"O"
             }
            ),
    "WBS" : ("Wishbone Slave",
             {"ADR":"I", "DAT":"IO", "WE":"I", "SEL":"i", "ACK":"O", "CYC":"I",
              "STB":"I"
             }
            ),
    "WBC" : ("Wishbone Clock and Reset", {"RST":"IO", "CLK":"IO"})
}

