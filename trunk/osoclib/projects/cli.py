#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Command line interpreter for Projects manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/05/21
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

__doc__ = "Command Line Interface for Orchestra projects manipulation."
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import sys
import os
import os.path as dir

from core import BaseCli, ArgsSet, Settings
from projects import *
from components import *

FILE_ARGS = ArgsSet(name=None, force=False)
COMPONENT_ARGS = ArgsSet(name=None, base=None)
CREATION_ARGS = ArgsSet(name="New Project", version="1.0", author="", board="apf9328", description=None)
EDITION_ARGS = ArgsSet(name=None, version=None, author=None, board=None, description=None)
INSTANCE_ARGS = ArgsSet(name=None)
CLOCK_ARGS = ArgsSet(name=None, frequency=50000000, type="static")
GENERIC_ARGS = ArgsSet(name=None, value=None)
INTERFACE_ARGS = ArgsSet(name=None, offset=None, link=None)

settings = Settings()

class ProjectComponentGenericCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all component instance generics settings
        """
        for gen in self.generics:
            self.write("name=%s value=%s\n" % (gen.name, gen.value))
        
    def do_edit(self, arg):
        """\nEdit generic settings.
        
        edit name=<string> value=<string>
        
            name - generic parameter name
            value - generic parameter new value
        """

        args = GENERIC_ARGS.parse(arg)
        try:
            if args.name and args.value:
                (gen, subelem) = self.generics.getElement(args.name)
                if gen:
                    gen.value = args.value
                    self.write("Generic '%s' changed to '%s'.\n" % (gen.name, gen.value))
                else:
                    self.write("Generic '%s' not found, operation canceled.\n" % args.name)
        except:
            self.write("*** Arguments error, operation canceled.\n")
        
class ProjectComponentInterfaceCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all component instance interfaces settings
        """
        for iface in self.interfaces:
            self.write("name=%s offset=%s link=%s\n" % (iface.name, iface.offset, iface.link))

    def do_edit(self, arg):
        """\nEdit interface settings.
        
        edit name=<string> offset=<string> link=<string>
        
            name - interface parameter name
            offset - interface offset new value
            link - interface link new value
        """

        args = INTERFACE_ARGS.parse(arg)
        try:
            if args.name and (args.offset or args.link):
                (iface, subelement) = self.interfaces.getElement(args.name)
                if iface:
                    if(args.offset):
                        iface.offset = args.offset
                    else:
                        iface.offset = ""
                    if(args.link):
                        iface.link = iface.link
                    else:
                        iface.link = ""
                        
                    self.write("Interface '%s' successfully changed.\n" % args.name)
                else:
                    self.write("Interface '%s' not found, operation canceled.\n" % args.name)
                    
                return
        except:
            pass
        
        self.write("*** Arguments error, operation canceled.\n")

class ProjectComponentCli(BaseCli):
    def do_dir(self, arg):
        """\nDisplay available components.
        """
        comp_dir = settings.components_dir
        for file in os.listdir(comp_dir):
            name = dir.join(comp_dir, file)
            if(dir.isfile(name)):
                cp = Component(name)
                self.write("Name = %s, Version = %s, Category = %s\n" % (cp.name, cp.version, cp.category))

    def do_xml(self, arg):
        """\nDisplay project components in XML format.
        
        xml [arg]
        
            arg = optional instance name
        """
        self.write(settings.active_project.asXML())

    def do_list(self, arg):
        """\nDisplay all component instances from active project.
        """
        for (cp,prop) in settings.active_project.components:
            self.write("name = %s, base = %s\n"%(cp.name,cp.base))

    def do_add(self, arg):
        """\nAdd component to current project.

        add name=<string> base=<string>

            name  = new component instance name.
            base  = component name.
        """
        args = COMPONENT_ARGS.parse(arg)
        if args:
            try:
                cp = getMatchingComponent(settings.components_dir, args.base)

                if cp is None:
                    self.write("*** No component '%s' found, component addition canceled\n" % args.base)
                else:
                    settings.active_project.addComponent(args.name, cp)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Component '%s' succproessfully added as '%s'.\n" % (args.base, dir.basename(args.name)))
        else:
            self.write("*** Arguments extraction error, component addition canceled.\n")


    def do_del(self, arg):
        """\nRemove component instance from current project.

        del <string>

            <string> is instance name to remove.
        """

        name = arg
        try:
            name = INSTANCE_ARGS.parse(arg).name
        except:
            pass
            
        if name:
            try:
                settings.active_project.removeComponent(name)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Instance '%s' successfully removed.\n" % name)
        else:
            self.write("*** Argument error, instance deletion canceled.\n")
            
    def do_rename(self, arg):
        """\nChange instance name.
        
        rename <old_name> <new_name>
        
            <old_name> is current instance name.
            <new_name> is new instance name.
        """
        
        arg = str(arg).lower().split()
        
        if len(arg) <= 1:
            self.write("*** Parameters error, operation canceled.\n")
            return
        
        if settings.active_project is None:
            self.write("*** No open project, operation canceled.\n")
        else:
            instance = settings.active_project.findComponent(arg[0])
            if settings.active_project.findComponent(arg[1]) is None:
                instance.name = arg[1]
                self.write("Name changed from '%s' to '%s' (base is %s).\n" % (arg[0], arg[1], instance.base))
            else:
                self.write("*** Component '%s' already exist, operation canceled.\n" % arg)

    def do_generics(self, arg):
        """\nEdit selected instance generics parameters.
        
        generics <string> [arg]

            <string>  name of instance to manipulate
            no arg -> launch component instance generics management shell.
            arg    -> execute [arg] component instance generics command.        
        """

        args = str(arg).split()
        name = None
        try:
            name = args[0]
        except:
            pass
                
        if name:
            cp = settings.active_project.findComponent(name)
        else:
            self.write("*** Argument error, generics manipulation canceled.\n")
            return

        settings.project_component = cp
        
        if cp:
            if len(cp[1]["generics"]) > 0:
                cli = ProjectComponentGenericCli(self)
                cli.generics = cp[1]["generics"]
                cli.setPrompt("generics")
                arg = " ".join(args[1:])
                if len(arg) > 0:
                    line = cli.precmd(arg)
                    cli.onecmd(line)
                    cli.postcmd(True, line)
                else:
                    cli.cmdloop()
                    self.stdout.write("\n")
            else:
                self.write("*** Instance named '%s' hasn't generics, operation canceled.\n" % name)
        else:
            self.write("*** No component instance named '%s' found, generics manipulation canceled.\n" % name)
    
    def do_interfaces(self, arg):
        """\nEdit selected instance interfaces parameters.
        
        interfaces <string> [arg]

            <string>  name of instance to manipulate
            no arg -> launch component instance interfaces management shell.
            arg    -> execute [arg] component instance interfaces command.        
        """

        args = str(arg).split()
        name = None
        try:
            name = args[0]
        except:
            pass
        
        if name:
            cp = settings.active_project.findComponent(name)
        else:
            self.write("*** Argument error, interfaces manipulation canceled.\n")
            return

        settings.project_component = cp

        if cp:
            if len(cp[1]["interfaces"]) > 0:
                cli = ProjectComponentInterfaceCli(self)
                cli.interfaces = cp[1]["interfaces"]
                cli.setPrompt("interfaces")
                arg = " ".join(args[1:])
                if len(arg) > 0:
                    line = cli.precmd(arg)
                    cli.onecmd(line)
                    cli.postcmd(True, line)
                else:
                    cli.cmdloop()
                    self.stdout.write("\n")
            else:
                self.write("*** Instance named '%s' hasn't interfaces, operation canceled.\n" % name)
        else:
            self.write("*** No component instance named '%s' found, interfaces manipulation canceled.\n" % name)
    
class ProjectsCli(BaseCli):
    def do_xml(self, arg):
        """\nDisplay XML description from current project or from specified project.
        """

        name = arg
        try:
            name = FILE_ARGS.parse(arg).name
        except:
            pass

        if name:
            cp = Component(filename=dir.join(settings.components_dir, name))
        else:
            cp = settings.active_project

        if cp:
            self.write(str(cp))

    def do_create(self, arg):
        """\nCreate a new project from scratch.
        
        create name=<string> [board=<string>] [version=<string>] [author=<string>]

            name     = new project name. Default = New Project.
            board    = project target board. Default = APF9328.
            version  = project version. Default = 1.0.
            author   = component category. Default = User Component.
        """
        args = CREATION_ARGS.parse(arg)
        if args:
            proj = Project()
            proj.name = args.name
            proj.version =  args.version
            proj.category = args.category
            self.write("New project created.\n")
            settings.active_project = proj
        else:
            self.stdout.write("*** Arguments extraction error, creation canceled.\n")

    def do_edit(self, arg):
        """\nOpen a existing project for modification.
        
        edit <string>

            <string> = Project name. Project must be in projects directory when 
                       full name not specified.
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
            self.write("Project '%s', version '%s', category '%s' ready for edition.\n" % (cp.name, cp.version, cp.category))
        else:
            self.write("*** Project '%s' not found. Edition canceled.\n")

    def do_close(self, arg):
        """\nCancel current component edition.
        """
        settings.active_component = None

    def do_save(self, arg):
        """\nSave current project modifications.
        
        save [name=<string>] [--force]

            name = Project name (without extension).
            force = Force project overwriting if already exist.
        """
        
        if not settings.active_component:
            self.write("*** No project edition in progression.\n")
            return
        
        force = False
        name = os.path.basename(settings.active_project.filename)
        if arg:
            try:
                args = FILE_ARGS.parse(arg)
                name = args.name
                force = args.force
            except:
                self.write("*** Arguments parsing error. Project saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Project saving canceled.\n")
            return
            
        archive=dir.join(os.curdir, name) + ".xml"
        if name != settings.active_project.filename:
            if dir.exists(archive) and not force:
                self.write("*** A project named '%s' already exists. Project saving canceled.\n" % archive)
                return
            settings.active_project.filename = name
            
        settings.active_project.save(archive)
        self.write("Project saved as '%s'\n" % archive)

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
            self.write("*** No open project.\n")

    def do_name(self, arg):
        """\nDisplay or modify current project name.
        
        name [<string>]

            <string> = New name.
        """
        if settings.active_project:
            if arg:
                arg = str(arg).strip()
                old = settings.active_project.name
                settings.active_project.name = arg
                self.write("Name changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_project.name)
        else:
            self.write("*** No open project.\n")

    def do_components(self, arg):
        """\nComponents manipulation commands.
        
        components [arg]

            no arg -> launch project components management shell.
            arg    -> execute [arg] component command.
        """

        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return

        cli = ProjectComponentCli(self)
        cli.setPrompt("components")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_check(self, arg):
        """\nCheck current project for errors.
        """
        pass
    
    def do_routes(self, arg):
        """\nSystem on Chip routes manipulation commands.
        
        routes [arg]

            no arg -> launch SoC routes management shell.
            arg    -> execture [arg] SoC routes command.
        """
        pass

    def do_clocks(self, arg):
        """\nSystem on Chip clocks manipulation commands.

        clocks [arg]
        
            no arg -> launch SoC clocks management shell.
            arg    -> execture [arg] SoC clocks command.
        """
        pass
