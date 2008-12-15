#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     utils.py
# Purpose:  Helper functions
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/12/14
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

__doc__ = "Some helper functions"
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"


def to_boolean(arg):
    if isinstance(arg, bool):
        return arg

    if isinstance(arg, int):
        return bool(arg)
    
    arg = str(arg).strip().lower()
    if len(arg) < 1:
        return False
    
    if arg[0] in ['t', '1', 'y']:
        return True
    
    return False
