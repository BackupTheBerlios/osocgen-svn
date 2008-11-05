#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Command line interpreter for Projects manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/05/21
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

class ProjectCompoentCli(BaseCli):
    def do_add(self, arg):
        """\nAdd component to current project.

        add name=<string> base=<string>

            name  = new component instance name.
            base  = component name.
        """
        args = COMPONENT_ARGS.parse(arg)
        if args:
            try:
                settings.active_project.addComponent(args.name, args.base)
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

    def do_list(self, arg):
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
        """\nCreate a new project from scratch.
        create [name=<string>] [version=<string>] [category=<string>]

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
        if settings.active_project:
            if arg:
                arg = str(arg).strip()
                old = settings.active_project.name
                settings.active_project.name = arg
                self.write("Name changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_project.name)
        else:
            self.write("*** No project opened for edition.\n")

    def do_hdl(self, arg):
        """\nhdl [arg] : component HDL files manipulation commands.

        no arg -> launch Components HDL files managment shell.
        arg    -> execture [arg] HDL files command.
        """

        if not settings.active_project:
            self.write('*** No project selected, action canceled.\n')
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

        no arg -> launch Components Driver files managment shell.
        arg    -> execture [arg] Driver command.
        """

        pass

    def do_register(self, arg):
        """\nregister [arg] : component registers manipulation commands.

        no arg -> launch Components Registers managment shell.
        arg    -> execture [arg] Register command.
        """

        pass

    def do_interface(self, arg):
        """\ninterface [arg] : component Wihsbone Interfaces manipulation commands.

        no arg -> launch Components Wihsbone Interfaces managment shell.
        arg    -> execture [arg] Interface command.
        """

        pass
