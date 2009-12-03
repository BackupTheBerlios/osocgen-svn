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

"Command Line Interface for Orchestra Components/IPs manipulation."

__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os
import os.path as path

from core import BaseCli, ArgsSet, Settings, format_table
from components import Component, ComponentError

CREATION_ARGS = ArgsSet(name="New Component", version="1.0", category="User Component", description=None)
EDITION_ARGS = ArgsSet(name=None, version=None, category=None, description=None)
HDL_ARGS = ArgsSet(name=None, scope="all", order=0, istop=False)
FILE_ARGS = ArgsSet(name=None, force=False)
ATTACHED_ARGS = ArgsSet(name=None, iface=False)
IFACE_ARGS = ArgsSet(name=None, type="GLS", clockandreset=None)

# Get current session settings
settings = Settings()

class ComponentsInterfaceCli(BaseCli):
    def do_list(self, arg):
        """\nDisplay all interfaces exposed by component.
        """
        # pylint: disable-msg=W0613
        titles = ["name", "type", "clockandreset"]
        rows = []
        for iface in settings.active_component.interfaces.iteritems():
            rows.append([iface.name, iface.type, iface.clockandreset])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")
            
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
        except AttributeError:
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
        # pylint: disable-msg=W0613
        settings.active_component.cleanInterfaces()
        
    def do_attached(self, arg):
        """\nList all ports or interfaces attached to an interface
        
            attached [name=]<string> [--iface]
            
                string = interface name to analyze
                iface = flag to search for attached interfaces
        """
        
        args = ATTACHED_ARGS.parse(arg)
        if args:
            name = args.name
            iface = args.iface
        else:
            name = arg
            iface = False

        if name:
            try:
                (source, attached) = self.component.getAttached(name, iface)
            except ComponentError, e:
                self.write(e.message)
            else:
                titles = ["name", "type"]
                rows = []
                if iface:
                    self.write("Interfaces attached to interface '%s' (type = %s):\n" % (name, source.type))
                    name = name.lower()
                    for iface in attached:
                        if iface.clockandreset:
                            if iface.clockandreset.lower() == name:
                                rows.append([iface.name, iface.type])
                else:
                    self.write("Ports attached to interface '%s' (type = %s):\n" % (name, source.type))
                    for port in attached:
                        if port.interface.lower() == name:
                            rows.append([port.name, port.type])
                
                # Create table and display it
                self.write("\n".join(format_table(titles, rows)))
                self.write("\n")
        else:
            self.write("*** Argument error, operation canceled.\n")

class ComponentsHdlCli(BaseCli):
    def do_add(self, arg):
        """\nAdd new HDL file to current component.

        add name=<string> [scope=<string>] [order=<integer>] [--istop|istop=True/False/1/0]

            name  = hdl file name. REQUIRED.
            scope = scope of this file (e.g. all, altera, xilinx, testbench). Default = all.
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
        except AttributeError:
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
        # pylint: disable-msg=W0613
        titles = ["name", "scope", "order", "is top"]
        rows = []
        for hdl_file in settings.active_component.hdl_files.iteritems():
            rows.append([hdl_file.name, hdl_file.scope, hdl_file.order, 
                         hdl_file.istop])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")

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
        except AttributeError:
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
    multiline_commands = ['description']
    
    def do_xml(self, arg):
        """\nDisplay XML description from current component or from specified component.
        """

        try:
            name = FILE_ARGS.parse(arg).name
        except AttributeError:
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
        # pylint: disable-msg=W0613
        titles = ["name", "version", "category"]
        rows = []
        comp_dir = settings.components_dir
        for cp_file in os.listdir(comp_dir):
            name = path.join(comp_dir, cp_file)
            if(path.isfile(name)):
                cp = Component(name)
                rows.append([cp.name, cp.version, cp.category])
        self.write("\n".join(format_table(titles, rows)))
        self.write("\n")

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
        except AttributeError:
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
        # pylint: disable-msg=W0613
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
            except AttributeError:
                self.write("*** Arguments parsing error. Component saving canceled.\n")
                return
        
        if not name:
            self.write("*** No file name specified. Component saving canceled.\n")
            return
            
        archive = path.join(settings.components_dir,name)
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

    def do_description(self, arg):
        """\nDisplay or modify current component description.
This is a multiline command , to terminate the command the last line must be 
only a point.

        description [<string>]

            <string> = New description.
        """
        if settings.active_component:
            if arg:
                arg = str(arg).strip()
                settings.active_component.description = arg
                self.write("Description changed.\n")
            else:
                self.write("%s\n" % settings.active_component.description)
        else:
            self.write("*** No open component.\n")
    
    def do_check(self, arg):
        """\nCheck active component for errors.
        """
        # pylint: disable-msg=W0613
        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return
        
        errors = settings.active_component.check()
        if errors:
            self.write("\n".join(errors))
            self.write("\n")
        else:
            self.write("No error\n")

    def do_hdl(self, arg):
        """\nComponent HDL files manipulation commands.

        hdl [arg]
        
            no arg -> launch Components HDL files management shell.
            arg    -> execute [arg] HDL files command.
        """

        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return

        cli = ComponentsHdlCli(self)
        cli.setPrompt("hdl")
        cli.component = settings.active_component
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")
            
    def do_drivers(self, arg):
        """\nComponent software driver files manipulation commands.

        drivers [arg]
        
            no arg -> launch Components Driver files management shell.
            arg    -> execute [arg] Driver command.
        """

        pass

    def do_registers(self, arg):
        """\nComponent registers manipulation commands.

        registers [arg]
        
            no arg -> launch Components Registers management shell.
            arg    -> execute [arg] Register command.
        """

        pass

    def do_interfaces(self, arg):
        """\nComponent Wishbone Interfaces manipulation commands.

        interfaces [arg]
        
            no arg -> launch Components Wishbone Interfaces management shell.
            arg    -> execute [arg] Interface command.
        """

        if not settings.active_component:
            self.write('*** No component selected, action canceled.\n')
            return

        cli = ComponentsInterfaceCli(self)
        cli.setPrompt("interfaces")
        cli.component = settings.active_component
        if arg:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")
