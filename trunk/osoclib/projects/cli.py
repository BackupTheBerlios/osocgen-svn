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

settings = Settings()

class ProjectComponentCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay available components.
        """
        comp_dir = settings.components_dir
        for file in os.listdir(comp_dir):
            name = dir.join(comp_dir, file)
            if(dir.isfile(name)):
                cp = Component(name)
                self.write("Name = %s, Version = %s, Category = %s\n" % (cp.name, cp.version, cp.category))

    def do_add(self, arg):
        """\nAdd component to current project.

        add name=<string> base=<string>

            name  = new component instance name.
            base  = component name.
        """
        args = COMPONENT_ARGS.parse(arg)
        if args:
            try:
                comp_dir = settings.components_dir
                cp = None
                for file in os.listdir(comp_dir):
                    name = dir.join(comp_dir, file)
                    if(dir.isfile(name)):
                        cp = Component(name)
                        if cp.name == args.base:
                            break
                    else:
                        cp = None
                
                if cp is None:
                    self.write("*** No component '%s' found, component addition canceled\n" % args.base)
                else:
                    settings.active_project.addComponent(args.name, cp)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Component '%s' successfully added as '%s'.\n" % (dir.basename(args.name), args.base))
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

    def do_list2(self, arg):
        """\nDisplay instances from current project.
        """
        for file in settings.active_component.hdl_files:
            self.write("Name : %s, scope : %s, order : %d, istop : %d\n" % (file.name, file.scope, file.order, file.istop))

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

    def do_component(self, arg):
        """\nComponent manipulation commands.
        
        component [arg]

            no arg -> launch Components HDL files management shell.
            arg    -> execture [arg] HDL files command.
        """

        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return

        cli = ProjectComponentCli(self)
        cli.setPrompt("component")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_route(self, arg):
        """\ndriver [arg] : component software driver files manipulation commands.

            no arg -> launch Components Driver files management shell.
            arg    -> execture [arg] Driver command.
        """

        pass

    def do_clock(self, arg):
        """\nregister [arg] : component registers manipulation commands.

            no arg -> launch Components Registers management shell.
            arg    -> execture [arg] Register command.
        """

        pass

