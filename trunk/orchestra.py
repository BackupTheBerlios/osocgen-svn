#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     <module_name>
# Purpose:  <Description>
#
# Author:   Fabrice MOUSSET
#
# Created:  2007/04/03
# Licence:  GPLv3 or newer
#-----------------------------------------------------------------------------
# Revision list :
#
# Date       By        Changes
#
#-----------------------------------------------------------------------------

__doc__ = ""
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import sys
import os.path as dir
import os

if not hasattr(sys, "frozen"):
    dirname = dir.join(dir.dirname(dir.realpath(__file__)),"osoclib")
    sys.path.append(dirname)

from osoclib import OrchestraCli

if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-i", "--interactive", action="store_true")
    options, args = parser.parse_args()
    cli = OrchestraCli()
    try:
        filename, = args
    except ValueError:
        pass
    else:
        if (os.path.isfile(filename)):
            cli.stdin = file(filename)
            cli.use_rawinput = False
        else:
            print ("File '%s' don't exist!\n" % filename)

    cli.cmdloop()
