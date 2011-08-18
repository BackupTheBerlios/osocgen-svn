#! /usr/bin/python
# -*- coding: utf-8 -*-
#===============================================================================
# Name:     cli.py
# Purpose:  Command line interpreter for Targets manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2009/05/04
# License:  GPLv3 or newer
#===============================================================================
# Last commit info:
# 
# $LastChangedDate:: xxxx/xx/xx xx:xx:xx $
# $Rev::                                 $
# $Author::                              $
#===============================================================================
# Revision list :
#
# Date       By        Changes
#
#===============================================================================

"Command Line Interface for Orchestra targets manipulation."

__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os.path as path

from core import BaseCli, ArgsSet, Settings, format_table
from targets import Target, TargetError

NAME_ARGS = ArgsSet(name=None)
FILE_ARGS = ArgsSet(name=None, force=False)
CREATION_ARGS = ArgsSet(name="New Target", version="1.0", author="", model="", 
                        manufacturer="", description=None)

# Getting access to application settings
settings = Settings() 

def extract_name(arg):
    args = NAME_ARGS.parse(arg)
    if args:
        return args.name
    return arg

class TargetsCli(BaseCli):
    multiline_commands = ['description']
    
    def do_create(self, arg):
        """\nCreate a new target from scratch.
        
        create name=<string> [version=<string>] [author=<string>] [model=<string>] [manufacturer=<string>]  

            name       = new target name. Default = New Target.
            version    = project version. Default = 1.0.
            author     = target creator. Default = Empty
            vendor     = CPLD/FPGA manufacturer (eg Xilinx, Altera). Default = Empty
            family     = CPLD/FPGA model (eg Spartan, Cyclone). Default = Empty
            speed      = CPLD/FPGA speed grade. Default = Empty
            package    = CPLD/FPGA packaging information. Default = Empty
            device     = CPLD/FPGA device reference (eg xc3s200, ep2c25). Default = Empty
        """
        args = CREATION_ARGS.parse(arg)
        if args:
            target = Target()
            target.name = args.name
            target.version =  args.version
            target.author = args.author
            target.model = args.model
            target.manufacturer = args.manufacturer
            self.write("New target created.\n")
            settings.active_target = target
        else:
            self.stdout.write("*** Arguments extraction error, creation canceled.\n")

    def do_edit(self, arg):
        """\nOpen a existing target for modification.
        
        edit <string>

            <string> = Target name. Target must be in targets sub-directory when 
                       full name not specified.
        """

        name = extract_name(arg)

        # Append project sub-directory if no path specified
        fpath, fname = path.split(name)
        if not fpath:
            name = path.join(settings.target_dir, fname)
        
        # Append default extension if not present
        if not name.lower().endswith(".xml"):
            name += ".xml"
            
        # Open project if file exist
        if(path.isfile(name)):
            target = Target(name)
            settings.active_target = target
            self.write("Target '%s', version '%s'  ready for edition.\n" % 
                       (target.name, target.version))
        else:
            self.write("*** Target '%s' not found. Edition canceled.\n" % name)

    do_open = do_edit
    
    def do_close(self, arg):
        """\nCancel current target edition.
        """
        # pylint: disable-msg=W0613
        if settings.active_target:
            self.write("*** Target '%s' is closed, changes are lost.\n" % 
                       settings.active_target.name)
        settings.active_target = None

    def do_save(self, arg):
        """\nSave current target modifications.
        
        save [name=<string>] [--force]

            name = Target name (without extension).
            force = Force target overwriting if already exist.
        """
        
        if not settings.active_target:
            self.write("*** No target edition in progression.\n")
            return
        
        force = False
        name = settings.active_target.filename
            
        if arg:
            try:
                args = FILE_ARGS.parse(arg)
                name = args.name
                force = args.force
            except AttributeError:
                self.write("*** Arguments parsing error. Target saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Target saving canceled.\n")
            return
            
        fpath, fname = path.split(name)
        
        # Append default extension if not present
        if not fname.lower().endswith(".xml"):
            fname = fname.split(".")
            if len(fname) > 1:
                fname = ".".join(fname.split(".")[:-1])
            else:
                fname = fname[0]
            fname += ".xml"

        # Append project sub-directory if no path specified
        if not fpath:
            name = path.join(settings.target_dir, fname)
        else:
            name = path.join(fpath, fname)

        # Check if new file name
        if name != settings.active_target.filename:
            # If file already exist, only overwrite if authorization is given 
            if path.exists(name) and not force:
                self.write("*** A target named '%s' already exists. Project saving canceled.\n" % name)
                return
            
            # Save new project file name
            settings.active_target.filename = name
            
        # Finally, save project
        settings.active_target.save(name)
        self.write("Target saved as '%s'\n" % name)

    def do_version(self, arg):
        """\nDisplay or modify current target version.
        
        version [<string>]

            <string> = New version.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.version
                settings.active_target.version = arg
                self.write("Version changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.version)
        else:
            self.write("*** No open target.\n")

    def do_name(self, arg):
        """\nDisplay or modify current target name.
        
        name [<string>]

            <string> = New name.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.name
                settings.active_target.name = arg
                self.write("Name changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.name)
        else:
            self.write("*** No open target.\n")

    def do_author(self, arg):
        """\nDisplay or modify current target author.
        
        author [<string>]

            <string> = New author name.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.author
                settings.active_target.author = arg
                self.write("Author changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.author)
        else:
            self.write("*** No open target.\n")

    def do_description(self, arg):
        """\nDisplay or modify current target description.
This is a multiline command , to terminate the command the last line must be 
only a point.

        description [<string>]

            <string> = New description.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                settings.active_target.description = arg
                self.write("Description changed.\n")
            else:
                self.write("%s\n" % settings.active_target.description)
        else:
            self.write("*** No open target.\n")
    
    def do_device(self, arg):
        """\nDisplay or modify current target CPLD/FPGA device reference.
        
        device [<string>]

            <string> = New device reference.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.device
                settings.active_target.device = arg
                self.write("Device changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.device)
        else:
            self.write("*** No open target.\n")

    def do_vendor(self, arg):
        """\nDisplay or modify current target CPLD/FPGA Manufacturer.
        
        vendor [<string>]

            <string> = New manufacturer.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.vendor
                settings.active_target.vendor = arg
                self.write("Vendor changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.vendor)
        else:
            self.write("*** No open target.\n")

    def do_family(self, arg):
        """\nDisplay or modify current target CPLD/FPGA device family.
        
        family [<string>]

            <string> = New family.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.family
                settings.active_target.family = arg
                self.write("Family changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.family)
        else:
            self.write("*** No open target.\n")

    def do_speed(self, arg):
        """\nDisplay or modify current target CPLD/FPGA speed grade.
        
        speed [<string>]

            <string> = New speed grade.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.speed
                settings.active_target.speed = arg
                self.write("Speed changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.speed)
        else:
            self.write("*** No open target.\n")

    def do_package(self, arg):
        """\nDisplay or modify current target CPLD/FPGA packaging information.
        
        package [<string>]

            <string> = New package.
        """
        if settings.active_target:
            if arg:
                arg = str(arg).strip()
                old = settings.active_target.package
                settings.active_target.package = arg
                self.write("Package changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_target.package)
        else:
            self.write("*** No open target.\n")
