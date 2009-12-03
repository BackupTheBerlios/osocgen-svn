#! /usr/bin/python
# -*- coding: utf-8 -*-
#===============================================================================
# Name:     cli.py
# Purpose:  Command line interpreter for Projects manipulation
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/05/21
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

"Command Line Interface for Orchestra projects manipulation."

__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os
import os.path as path

from core import BaseCli, ArgsSet, Settings, purge_dir, format_table
from projects import Project, ProjectError
from components import Component, find_component

NAME_ARGS = ArgsSet(name=None)
FILE_ARGS = ArgsSet(name=None, force=False)
COMPONENT_ARGS = ArgsSet(name=None, base=None)
CREATION_ARGS = ArgsSet(name="New Project", version="1.0", author="", target="apf9328", description=None)
EDITION_ARGS = ArgsSet(name=None, version=None, author=None, target=None, description=None)
INSTANCE_ARGS = ArgsSet(name=None)
CLOCK_ARGS = ArgsSet(name=None, frequency=50000000, type="static")
GENERIC_ARGS = ArgsSet(name=None, value=None)
INTERFACE_ARGS = ArgsSet(name=None, offset=None, link=None)
WIRE_ARGS = ArgsSet(name=None, type=None)

# Getting access to application settings
settings = Settings()

def extract_name(arg):
    args = NAME_ARGS.parse(arg)
    if args:
        return args.name
    return arg

class ProjectsWireCli(BaseCli):
    project = None
    def do_list(self, arg):
        """\nDisplay all wires
        """
        # pylint: disable-msg=W0613
        pass
#        titles = ["name", "value"]
#        rows = []
#        for gen in self.project.routes.iteritems():
#            rows.append([gen.name, gen.value])
#        self.write("\n".join(format_table(titles, rows)))
#        self.write("\n")
        
    def do_edit(self, arg):
        """\nChange wire settings.
        
        edit name=<string> type=<string>
        
            name - wire name
            type - wire type
        """
        args = WIRE_ARGS.parse(arg)
        try:
            if args.name:
                (wire, _) = settings.active_project.wires.getElement(args.name)
                if wire:
                    wire.type = args.type
                    self.write("Wire '%s' type changed to '%s'.\n" % 
                               (wire.name, wire.value))
                else:
                    self.write("Wire '%s' not found, operation canceled.\n" %
                                args.name)
        except AttributeError:
            self.write("*** Arguments error, operation canceled.\n")
        
    def do_add(self, arg):
        """\nAdd new wire to project.
        
        add name=<string> type=<string>
        
            name - wire name
            type - wire type
        """
        args = WIRE_ARGS.parse(arg)
        if args:
            try:
                settings.active_project.addWire(args.name, args.value)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Wire '%s' successfully added.\n" % (args.name))
        else:
            self.write("*** Arguments error, operation canceled.\n")

    def do_del(self, arg):
        """\nRemove wire from project.
        
        del [name=]<string>
        
            name - wire name
        """
        name = extract_name(arg)
        if name:
            try:
                settings.active_project.removeWire(name)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Wire '%s' successfully removed.\n" % name)
        else:
            self.write("*** Arguments error, operation canceled.\n")
            
class ProjectsComponentGenericCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all component instance generics settings
        """
        # pylint: disable-msg=W0613
        titles = ["name", "value"]
        rows = []
        for gen in self.generics.iteritems():
            rows.append([gen.name, gen.value])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")
        
    def do_edit(self, arg):
        """\nEdit generic settings.
        
        edit name=<string> value=<string>
        
            name - generic parameter name
            value - generic parameter new value
        """

        args = GENERIC_ARGS.parse(arg)
        try:
            if args.name and args.value:
                (gen, _) = self.generics.getElement(args.name)
                if gen:
                    gen.value = args.value
                    self.write("Generic '%s' changed to '%s'.\n" % (gen.name, gen.value))
                else:
                    self.write("Generic '%s' not found, operation canceled.\n" % args.name)
        except AttributeError:
            self.write("*** Arguments error, operation canceled.\n")
        
class ProjectsComponentInterfaceCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all component instance interfaces settings
        """
        # pylint: disable-msg=W0613
        titles = ["name", "offset", "link"]
        rows = []
        for iface in self.interfaces.iteritems():
            rows.append([iface.name, iface.offset, iface.link])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")

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
                (iface, _) = self.interfaces.getElement(args.name)
                if iface:
                    if(args.offset):
                        iface.offset = args.offset
                    else:
                        iface.offset = ""
                    if(args.link):
                        iface.link = args.link
                    else:
                        iface.link = ""
                        
                    self.write("Interface '%s' successfully changed.\n" % args.name)
                else:
                    self.write("Interface '%s' not found, operation canceled.\n" % args.name)
                    
                return
        except AttributeError:
            pass
        
        self.write("*** Arguments error, operation canceled.\n")

class ProjectsComponentCli(BaseCli):
    def do_dir(self, arg):
        """\nDisplay available components.
        """
        # pylint: disable-msg=W0613
        titles = ["name", "version", "category"]
        rows = []
        comp_dir = settings.components_dir
        for fname in os.listdir(comp_dir):
            name = path.join(comp_dir, fname)
            if(path.isfile(name)):
                cp = Component(name)
                rows.append([cp.name, cp.version, cp.category])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")

    def do_xml(self, arg):
        """\nDisplay project components in XML format.
        
        xml [arg]
        
            arg = optional instance name
        """
        # pylint: disable-msg=W0613
        self.write(settings.active_project.asXML())

    def do_list(self, arg):
        """\nDisplay all component instances from active project.
        """
        # pylint: disable-msg=W0613
        titles = ["name", "base"]
        rows = []
        for cp in settings.active_project.components.iteritems():
            rows.append([cp.name, cp.base])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")

    def do_add(self, arg):
        """\nAdd component to current project.

        add name=<string> base=<string>

            name  = new component instance name.
            base  = component name.
        """
        args = COMPONENT_ARGS.parse(arg)
        if args:
            try:
                cp = find_component(settings.components_dir, args.base)

                if cp is None:
                    self.write("*** No component '%s' found, component addition canceled\n" % args.base)
                else:
                    settings.active_project.addComponent(args.name, cp)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Component '%s' successfully added as '%s'.\n" % (args.base, path.basename(args.name)))
        else:
            self.write("*** Arguments extraction error, component addition canceled.\n")


    def do_del(self, arg):
        """\nRemove component instance from current project.

        del <string>

            <string> is instance name to remove.
        """

        name = extract_name(arg)
            
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
        except IndexError:
            pass
                
        if name:
            cp = settings.active_project.findComponent(name)
        else:
            self.write("*** Argument error, generics manipulation canceled.\n")
            return

        settings.project_component = cp
        
        if cp:
            if len(cp[1]["generics"]) > 0:
                cli = ProjectsComponentGenericCli(self)
                cli.generics = cp[1]["generics"]
                cli.setPrompt("generics@%s"%name.lower())
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
        except IndexError:
            pass
        
        if name:
            cp = settings.active_project.findComponent(name)
        else:
            self.write("*** Argument error, interfaces manipulation canceled.\n")
            return

        settings.project_component = cp

        if cp:
            if len(cp[1]["interfaces"]) > 0:
                cli = ProjectsComponentInterfaceCli(self)
                cli.interfaces = cp[1]["interfaces"]
                cli.setPrompt("interfaces@%s"%name.lower())
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

class ProjectsClockCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all defined clock domains for this design.
        """
        # pylint: disable-msg=W0613
        titles = ["name", "frequency", "type"]
        rows = []
        for clock in settings.active_project.clocks.iteritem():
            rows.append([clock.name, clock.frequency, clock.type])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")
            
    def do_add(self, arg):
        """\nAdd clock domain to current project.

        add name=<string> frequency=<integer> type=static|pll

            name  = new clock domain name.
            frequency  = clock frequency in Hertz.
            type = 
        """
        args = CLOCK_ARGS.parse(arg)
        if args:
            try:
                settings.active_project.addClock(args.name, args.frequency, args.type)
            except ProjectError, e:
                self.write(e.message) 
        else:
            self.write("*** Arguments extraction error, clock domain addition canceled.\n")


    def do_del(self, arg):
        """\nRemove component instance from current project.

        del <string>

            <string> is instance name to remove.
        """

        name = extract_name(arg)
            
        if name:
            try:
                settings.active_project.removeClock(name)
            except ProjectError, e:
                self.write(e.message)
            else:
                self.write("Clock '%s' successfully removed.\n" % name)
        else:
            self.write("*** Argument error, clock deletion canceled.\n")
            
class ProjectsCli(BaseCli):
    multiline_commands = ['description']
    
    def do_xml(self, arg):
        """\nDisplay XML description from current project or from specified project.
        """
        name = extract_name(arg)
        if name:
            cp = Component(filename=path.join(settings.components_dir, name))
        else:
            cp = settings.active_project

        if cp:
            self.write(str(cp))

    def do_create(self, arg):
        """\nCreate a new project from scratch.
        
        create name=<string> [target=<string>] [version=<string>] [author=<string>]

            name     = new project name. Default = New Project.
            target   = project target FPGA/CPLD. Default = APF9328.
            version  = project version. Default = 1.0.
            author   = component category. Default = User Component.
        """
        args = CREATION_ARGS.parse(arg)
        if args:
            proj = Project()
            proj.name = args.name
            proj.version =  args.version
            proj.category = args.category
            proj.target = args.target
            self.write("New project created.\n")
            settings.active_project = proj
        else:
            self.stdout.write("*** Arguments extraction error, creation canceled.\n")

    def do_edit(self, arg):
        """\nOpen a existing project for modification.
        
        edit <string>

            <string> = Project name. Project must be in projects sub-directory when 
                       full name not specified.
        """

        name = extract_name(arg)

        # Append project sub-directory if no path specified
        fpath, fname = path.split(name)
        if not fpath:
            name = path.join(settings.project_dir, fname)
        
        # Append default extension if not present
        if not name.lower().endswith(".prj"):
            name += ".prj"
            
        # Open project if file exist
        if(path.isfile(name)):
            cp = Project(name)
            settings.active_project = cp
            self.write("Project '%s', version '%s', target '%s' ready for edition.\n" % (cp.name, cp.version, cp.target))
        else:
            self.write("*** Project '%s' not found. Edition canceled.\n" % name)

    do_open = do_edit
    
    def do_close(self, arg):
        """\nCancel current component edition.
        """
        # pylint: disable-msg=W0613
        if settings.active_project:
            self.write("*** Project '%s' is closed, changes are lost.\n" % settings.active_project.name)
        settings.active_project = None

    def do_save(self, arg):
        """\nSave current project modifications.
        
        save [name=<string>] [--force]

            name = Project name (without extension).
            force = Force project overwriting if already exist.
        """
        
        if not settings.active_project:
            self.write("*** No project edition in progression.\n")
            return
        
        force = False
        name = settings.active_project.filename
            
        if arg:
            try:
                args = FILE_ARGS.parse(arg)
                name = args.name
                force = args.force
            except AttributeError:
                self.write("*** Arguments parsing error. Project saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Project saving canceled.\n")
            return
            
        fpath, fname = path.split(name)
        
        # Append default extension if not present
        if not fname.lower().endswith(".prj"):
            fname = fname.split(".")
            if len(fname) > 1:
                fname = ".".join(fname.split(".")[:-1])
            else:
                fname = fname[0]
            fname += ".prj"

        # Append project sub-directory if no path specified
        if not fpath:
            name = path.join(settings.project_dir, fname)
        else:
            name = path.join(fpath, fname)

        # Check if new file name
        if name != settings.active_project.filename:
            # If file already exist, only overwrite if authorization is given 
            if path.exists(name) and not force:
                self.write("*** A project named '%s' already exists. Project saving canceled.\n" % name)
                return
            
            # Save new project file name
            settings.active_project.filename = name
            
        # Finally, save project
        settings.active_project.save(name)
        self.write("Project saved as '%s'\n" % name)

    def do_version(self, arg):
        """\nDisplay or modify current project version.
        
        version [<string>]

            <string> = New version.
        """
        if settings.active_project:
            if arg:
                arg = str(arg).strip()
                old = settings.active_project.version
                settings.active_project.version = arg
                self.write("Version changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_project.version)
        else:
            self.write("*** No open project.\n")

    def do_description(self, arg):
        """\nDisplay or modify current project description.
This is a multiline command , to terminate the command the last line must be 
only a point.

        description [<string>]

            <string> = New description.
        """
        if settings.active_project:
            if arg:
                arg = str(arg).strip()
                settings.active_project.description = arg
                self.write("Description changed.\n")
            else:
                self.write("%s\n" % settings.active_project.description)
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

    def do_target(self, arg):
        """\nDisplay or modify current project target.
        
        target [<string>]
        
            <string> = New target.
        """
        if settings.active_project:
            if arg:
                arg = str(arg).strip()
                old = settings.active_project.target
                settings.active_project.name = arg
                self.write("target changed from '%s' to '%s'.\n" % (old, arg))
            else:
                self.write("%s\n" % settings.active_project.target)
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

        cli = ProjectsComponentCli(self)
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
        # pylint: disable-msg=W0613
        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return
        
        errors = settings.active_project.check(settings.components_dir)
        if len(errors) == 0:
            self.write("No errors.\n")
            return
        
        for category,errors in errors.iteritems():
            self.write('%s:\n' % category)
            for error in errors:
                self.write('  %s\n' % error)
        
    def do_compile(self, arg):
        """\nGenerate System on Chip.
        
        compile [arg]
        
            no arg -> compile project in default directory.
            arg    -> compile in specified directory. 
        """
        # pylint: disable-msg=W0613
        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return

        # Compilation steps
        self.write("INFO: Starting project '%s' compilation.\n" % settings.active_project.name)
        if not settings.active_project.filename:
            self.write("*** Project must be saved before compilation.")
            return
        
        # 1. Verify design parameters (check)
        errors = settings.active_project.check(settings.components_dir)
        if len(errors) > 0:
            self.write("*** Errors in project detected, compilation canceled.\n")
            return
        
        self.write("INFO: No errors detected.\n")
        
        # 2. Create/purge project directory
        out_dir = path.join(path.dirname(settings.active_project.filename), "output")
        if path.exists(out_dir):
            purge_dir(out_dir)
        else:        
            os.makedirs(out_dir)
        
        # 3. Call compilation routine
        settings.active_project.compile(settings.components_dir, out_dir)
    
    def do_wires(self, arg):
        """\nSystem on Chip wires manipulation commands.
        
        routes [arg]

            no arg -> launch SoC routes management shell.
            arg    -> execute [arg] SoC routes command.
        """
        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return

        cli = ProjectsWireCli(self)
        cli.setPrompt("wires")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_clocks(self, arg):
        """\nSystem on Chip clocks manipulation commands.

        clocks [arg]
        
            no arg -> launch SoC clocks management shell.
            arg    -> execute [arg] SoC clocks command.
        """
        if not settings.active_project:
            self.write('*** No open project, action canceled.\n')
            return

        cli = ProjectsClockCli(self)
        cli.setPrompt("clocks")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")
