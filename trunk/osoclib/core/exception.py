#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     exception.py
# Purpose:  Basic exception handler
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/03/25
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

"""Defines base classe for Orchestra exceptions.
"""

ERROR_INFO = 0
ERROR_CRITICAL = 1
ERROR_WARNING = 2

class Error(Exception):
    """Exception raised for errors.

    Attributes:
        ref -- exception value (default = -1)
        message -- textual explanation of the error
    """

    __slots__ = ['message', 'level']

    def __init__(self, message='', level=ERROR_INFO):
        self.level = level
        self.message = message
        Exception.__init__(self,message)
        
    def __repr__(self):
        return self.message
    
    __str__ = __repr__
