#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Command line interpreter for Components manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/1
# License:  GPLv3 or newer
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

import os
import os.path as path

from core import BaseCli, ArgsSet, Settings
from components import *

CREATION_ARGS = ArgsSet(name="New Component", version="1.0", category="User Component", description=None)
EDITION_ARGS = ArgsSet(name=None, version=None, category=None, description=None)
HDL_ARGS = ArgsSet(name=None, scope="all", order=0, istop=False)
FILE_ARGS = ArgsSet(name=None, force=False)
IFACE_ARGS = ArgsSet(name=None, type="GLS", clockandreset=None)

# Get current session settings
settings = Settings()

class ComponentsInterfaceCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all interfaces exposed by component.
        """
        for (iface, iface_param) in settings.active_component.interfaces:
            self.write("name=%s, type=%s, clockandreset=%s.\n" % (iface.name, iface.type, iface.clockandreset))
            
    def do_add(self, arg):
        """\nAdd new interface to the component.
        
        add name=<string> type=WBM|WBS|WBC|GLS clockandreset=<string>
        
            name = interface name. REQUIRED (must be unique)
            type = interface type (WBM, WBS, WBC or GLS allowed)
            clockandreset = clock domain for this interface (required for WBM or WBS interfaces).
        """
        args = IFACE_ARGS.parse(arg)
        if args:
            try:
                settings.active_component.addInterface(args.name, args.type, args.clockandreset)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("Interface '%s' successfully added.\n" % args.name)
        else:
            self.write("*** Arguments extraction error, interface addition canceled.\n")
        
    def do_del(self, arg):
        """\nRemove an interface from the component
        
        del <string>
        
            string = interface name
        """
        try:
            name = FILE_ARGS.parse(arg).name
        except:
            name = arg

        if name:
            try:
                settings.active_component.delInterface(name)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("Interface '%s' successfully removed.\n" % name)
        else:
            self.write("*** Argument error, interface deletion canceled.\n")
            
    def do_cleanup(self, arg):
        """\nRemove all unused interfaces from the component.
        """
        settings.active_component.cleanInterfaces()
        

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
            if "top" in args.keys():
                args["istop"] = args.top
            try:
                settings.active_component.addHdl(args.name, args.scope, args.order, args.istop)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("HDL file '%s' successfully added.\n" % path.basename(args.name))
        else:
            self.write("*** Arguments extraction error, file addition canceled.\n")


    def do_del(self, arg):
        """\nRemove HDL file from current component.

        del <string>

            <string> is hdl file name to remove.
        """

        try:
            name = FILE_ARGS.parse(arg).name
        except:
            name = arg
            
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
        for filenode in settings.active_component.hdl_files:
            file = filenode[0]
            self.write("Name : %s, scope : %s, order : %d, istop : %d\n" % (file.name, file.scope, file.order, file.istop))

    def do_order(self, arg):
        """\nDefine HDL files load order.
        """
        pass

    def do_top(self, arg):
        """\nSelect current component hdl top file.
        
        top <string>
        
            <string> is hld file name to set as top entity.
        """
        
        try:
            name = FILE_ARGS.parse(arg).name
        except:
            name = arg
            
        if name:
            try:
                settings.active_component.setTop(name)
            except ComponentError, e:
                self.write(e.message)
            else:
                self.write("HDL file '%s' is now to file.\n" % name)
        else:
            self.write("*** Argument error, file selection canceled.\n")
    
class ComponentsCli(BaseCli):
    def do_xml(self, arg):
        """\nDisplay XML description from current component or from specified component.
        """

        try:
            name = FILE_ARGS.parse(arg).name
        except:
            name = arg

        if name:
            cp = Component(filename=path.join(settings.components_dir, name))
        else:
            cp = settings.active_component

        if cp:
            self.write(str(cp))

    def do_list(self, arg):
        """\nDisplay available components.
        """
        comp_dir = settings.components_dir
        for file in os.listdir(comp_dir):
            name = path.join(comp_dir, file)
            if(path.isfile(name)):
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

        try:
            name = FILE_ARGS.parse(arg).name
        except:
            name = arg

        name = path.join(settings.components_dir,name) + ".zip"
        if(path.isfile(name)):
            cp = Component(name)
            settings.active_component = cp
            self.write("Component '%s', version '%s', category '%s' ready for edition.\n" % (cp.name, cp.version, cp.category))
        else:
            self.write("*** Component '%s' not found. Edition canceled.\n" % name)

    def do_close(self, arg):
        """\nCancel current component edition.
        """
        if settings.active_component:
            self.write("*** Component '%s' is closed, changes are lost.\n" % settings.active_component.name)
            
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
                name = args.name + ".zip"
                force = args.force
            except:
                self.write("*** Arguments parsing error. Component saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Component saving canceled.\n")
            return
            
        archive=path.join(settings.components_dir,name)
        if name != settings.active_component.filename:
            if path.exists(archive) and not force:
                self.write("*** A component named '%s' already exists. Component saving canceled.\n" % name[:-4])
                return
            settings.active_component.filename = name
            
        settings.active_component.save(archive)
        self.write("Component saved as '%s'\n" % name[:-4])

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
        """\nComponent HDL files manipulation commands.

        hdl [arg]
        
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
            
    def do_check(self, arg):
        """\nCheck active component for errors.
        """
        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return
        
        errors = settings.active_component.check()
        if errors:
            for message in errors:
                self.write(message)
        else:
            self.write("No error\n")

    def do_driver(self, arg):
        """\nComponent software driver files manipulation commands.

        driver [arg]
        
            no arg -> launch Components Driver files management shell.
            arg    -> execture [arg] Driver command.
        """

        pass

    def do_register(self, arg):
        """\nComponent registers manipulation commands.

        register [arg]
        
            no arg -> launch Components Registers management shell.
            arg    -> execture [arg] Register command.
        """

        pass

    def do_interfaces(self, arg):
        """\nComponent Wihsbone Interfaces manipulation commands.

        interfaces [arg]
        
            no arg -> launch Components Wihsbone Interfaces management shell.
            arg    -> execture [arg] Interface command.
        """

        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return

        cli = ComponentsInterfaceCli(self)
        cli.setPrompt("interfaces")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")
