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

import os
from os.path import join

def to_boolean(arg):
    """Convert any string or integer into boolean value."""
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

def purge_dir(basedir):
    """Purge directory structure."""

    if not os.path.exists(basedir):
        return
    
    for root, dirs, files in os.walk(basedir, topdown=False):
        for name in files:
            os.remove(join(root, name))
        for name in dirs:
            os.rmdir(join(root, name))

def format_table(titles, rows):
    """Format a table
    """
    
    # Initialize widths to have columns zero width to start with
    widths = [len(str(title)) for title in titles]
    
    # Adjust columns width to allow spaces for each row in turn
    for row in rows:
        widths = [max(w, len(str(item)))
                      for w, item in zip(widths, row)]
    
    # Create separator line
    separator = "".join(['+-' , '-+-'.join(['-' * w for w in widths]), '-+'])
    
    # Create result list
    table = []
    
    # Create title line
    line = "".join(['| ', ' | '.join([t.ljust(w).capitalize() 
                                      for t, w in zip(titles, widths)]), ' |'])
    table.append(separator)
    table.append(line)
    table.append(str(separator).replace('-', '='))
    
    # Add rows of data
    for row in rows:
        data = []
        for item, w in zip(row, widths):
            if item is None:
                data.append("".ljust(w))
            else:
                data.append(str(item).ljust(w))
        line = "".join(['| ', ' | '.join(data), ' |'])
        table.append(line)

    table.append(separator)
        
    return table

def cmp_stri(name_a, name_b):
    """Compare two string caseless."""
    if not name_a or not name_b:
        return False
    
    return str(name_a).strip().lower() == str(name_b).strip().lower()

def attr_property(getter_function):
    """Decorator function to allow access to complex properties.
    
Usage example:
    
    class Book(object)
    
        @attr_property
        def urls(self, name):
            if name == "absolute":
                pattern = "books-view"
            elif name == "reviews":
                pattern = "books-reviews"
            elif name == "delete":
                pattern = "books-delete"
                
            return reverse(pattern)
            
            
    b = Book()
    
    print b.urls["absolute"]
    print b.urls.absolute
    ...
    """
    class _Object(object):
        def __init__(self, obj):
            self.obj = obj
        def __getattr__(self, attr):
            return getter_function(self.obj, attr)
    
    return property(_Object)

def full_property(func):
    """Decorator function to define getter, setter and deller in one.
    
Usage example:

    class Person(object):
        @full_property
        def name(self):
            doc  = "The person's name"
            
            def fget(self):
                return "%s %s" % (self.first_name, self.last_name)
                
            def fset(self, name):
                self.first_name, self.last_name = name.split()
                
            def fdel(self, name):
                del self.first_name
                del self.last_name
    """
    return property(**func())
 
if __name__ == '__main__': 
    class Book(object):

        @attr_property
        def urls(self, write, name):
            if write:
                return
    
            if name == "absolute":
                pattern = "books-view"
            elif name == "reviews":
                pattern = "books-reviews"
            elif name == "delete":
                pattern = "books-delete"
                
            return pattern
        
        
    b = Book()
    
    print b.urls["absolute"]
    print b.urls.absolute
