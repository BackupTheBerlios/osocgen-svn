#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Command line interpreter for Components manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/1
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

__doc__ = "Command Line Interface for Armadeus Ready Components manipulation."
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import sys
import os
import os.path as dir

from core import BaseCli, ArgsSet, Settings
from components import *

CREATION_ARGS = ArgsSet(name="New Component", version="1.0", category="User Component", description=None)
EDITION_ARGS = ArgsSet(name=None, version=None, category=None, description=None)
HDL_ARGS = ArgsSet(name=None, scope="all", order=0, istop=False)
FILE_ARGS = ArgsSet(name=None, force=False)

settings = Settings()

class ComponentsHdlCli(BaseCli):
    def do_add(self, arg):
        """\nAdd new HDL file to current component.

        add name=<string> [scope=<string>] [order=<integer>] [--istop|istop=True/False/1/0]

            name  = hdl file name. REQUIRED.
            scope = scope of this file (e.g. all, xilinx, test). Default = all.
            order = load order in hdl project. By default it is file index.
            istop = file is top file of component. By default false. --istop equals istop=True
        """
        args = HDL_ARGS.parse(arg)
        if args:
            try:
                settings.active_component.addHdl(args.name, args.scope, args.order, args.istop)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("HDL file '%s' successfully added.\n" % dir.basename(args.name))
        else:
            self.write("*** Arguments extraction error, file addition canceled.\n")


    def do_del(self, arg):
        """\nRemove HDL file from current component.

        del <string>

            <string> is hdl file name to remove.
        """

        name = arg
        try:
            name = FILE_ARGS.parse(arg).name
        except:
            pass
            
        if name:
            try:
                settings.active_component.removeHdl(name)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("HDL file '%s' successfully removed.\n" % name)
        else:
            self.write("*** Argument error, file deletion canceled.\n")

    def do_list(self, arg):
        """\nDisplay HDL files from current component.
        """
        for file in settings.active_component.hdl_files:
            self.write("Name : %s, scope : %s, order : %d, istop : %d\n" % (file.name, file.scope, file.order, file.istop))

    def do_order(self, arg):
        """\nDefine HDL files load order.
        """
        pass

    def do_top(self, arg):
        """\nSelect current component hdl top file.
        """
        pass
    
class ComponentsCli(BaseCli):
    def do_xml(self, arg):
        """\nDisplay XML description from current component or from specified component.
        """

        name = arg
        try:
            name = FILE_ARGS.parse(arg).name
        except:
            pass

        if name:
            cp = Component(filename=dir.join(settings.components_dir, name))
        else:
            cp = settings.active_component

        if cp:
            self.write(str(cp))

    def do_list(self, arg):
        """\nDisplay available components.
        """
        comp_dir = settings.components_dir
        for file in os.listdir(comp_dir):
            name = dir.join(comp_dir, file)
            if(dir.isfile(name)):
                cp = Component(name)
                self.write("Name = %s, Version = %s, Category = %s\n" % (cp.name, cp.version, cp.category))

    def do_create(self, arg):
        """\nCreate a new component.
        create [name=<string>] [version=<string>] [category=<string>]

            name     = new component name. Default = New Component.
            version  = component version. Default = 1.0.
            category = component category. Default = User Component.
        """
        args = CREATION_ARGS.parse(arg)
        if args:
            comp = Component()
            comp.name = args.name
            comp.version =  args.version
            comp.category = args.category
            self.write("New component created.\n")
            settings.active_component = comp
        else:
            self.stdout.write("*** Arguments extraction error, creation canceled.\n")

    def do_edit(self, arg):
        """\nOpen a existing component for modification.
        edit <string>

            <string> = Component base name. Component MUST be in components directory.
        """

        name = arg
        try:
            args = FILE_ARGS.parse(arg).name
            
            if args.name:
                name = args.name
        except:
            pass

        name=dir.join(settings.components_dir,name) + ".zip"
        if(dir.isfile(name)):
            cp = Component(name)
            settings.active_component = cp
            self.write("Component '%s', version '%s', category '%s' ready for edition.\n" % (cp.name, cp.version, cp.category))
        else:
            self.write("*** Component '%s' not found. Edition canceled.\n")

    def do_close(self, arg):
        """\nCancel current component edition.
        """
        settings.active_component = None

    def do_save(self, arg):
        """\nSave current component modifications.
        save [name=<string>] [--force]

            name = Archive name (without extension).
            force = Force archive overwriting if already exist.
        """
        
        if not settings.active_component:
            self.write("*** No component edition in progression.\n")
            return
        
        force = False
        name = settings.active_component.filename
        if arg:
            try:
                args = FILE_ARGS.parse(arg)
                name = args.name
                force = args.force
            except:
                self.write("*** Arguments parsing error. Component saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Component saving canceld.\n")
            return
            
        archive=dir.join(settings.components_dir,name) + ".zip"
        if name != settings.active_component.filename:
            if dir.exists(archive) and not force:
                self.write("*** A component named '%s' already exists. Component saving canceled.\n" % name)
                return
            settings.active_component.filename = name
            
        settings.active_component.save(archive)
        self.write("Component saved as '%s'\n" % name)

    def do_version(self, arg):
        """\nDisplay or modify current component version.
        version [<string>]

            <string> = New version.
        """
        if settings.active_component:
            if arg:
                arg = str(arg).strip()
                old = settings.active_component.version
                settings.active_component.version = arg
                self.write("Version changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_component.version)
        else:
            self.write("*** No component opened for edition.\n")

    def do_category(self, arg):
        """\nDisplay or modify current component category.
        category [<string>]

            <string> = New category.
        """
        if settings.active_component:
            if arg:
                arg = str(arg).strip()
                old = settings.active_component.category
                settings.active_component.category = arg
                self.write("Category changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_component.category)
        else:
            self.write("*** No component opened for edition.\n")

    def do_name(self, arg):
        """\nDisplay or modify current component name.
        name [<string>]

            <string> = New name.
        """
        if settings.active_component:
            if arg:
                arg = str(arg).strip()
                old = settings.active_component.name
                settings.active_component.name = arg
                self.write("Name changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_component.name)
        else:
            self.write("*** No component opened for edition.\n")

    def do_hdl(self, arg):
        """\nhdl [arg] : component HDL files manipulation commands.

        no arg -> launch Components HDL files management shell.
        arg    -> execture [arg] HDL files command.
        """

        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return

        cli = ComponentsHdlCli(self)
        cli.setPrompt("hdl")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_driver(self, arg):
        """\ndriver [arg] : component software driver files manipulation commands.

        no arg -> launch Components Driver files management shell.
        arg    -> execture [arg] Driver command.
        """

        pass

    def do_register(self, arg):
        """\nregister [arg] : component registers manipulation commands.

        no arg -> launch Components Registers management shell.
        arg    -> execture [arg] Register command.
        """

        pass

    def do_interface(self, arg):
        """\ninterface [arg] : component Wihsbone Interfaces manipulation commands.

        no arg -> launch Components Wihsbone Interfaces management shell.
        arg    -> execture [arg] Interface command.
        """

        pass
