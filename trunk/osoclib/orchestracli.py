#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     Components.py
# Purpose:  Basic Command Line Interface for Orchestra elements
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/17
# Licence:  GPLv3 or newer
#=============================================================================
# Last commit info:
#
# $LastChangedDate:: xxxx/xx/xx xx:xx:xx $
# $Rev::                                 $
# $Author::                              $
#=============================================================================
# Revision list :
#
# Date       By        Changes
#
#=============================================================================

__doc__ = "Basic Command Line Interface"
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

if __name__ == "__main__":
    import os.path as dir
    import sys

    dirname, base = dir.split(dir.dirname(dir.realpath(__file__)))
    sys.path.append(dirname)

from core import BaseCli
from components import ComponentsCli
from projects import ProjectsCli
from targets import TargetsCli

class OrchestraCli(BaseCli):
    intro = """
        Orchestra command line interpreter.
        Type ? for help.\n"""

    def do_components(self, arg):
        """components [arg] : Orchestra Ready Components management commands.

        no arg -> launch Components management shell.
        arg    -> execute [arg] component command.
        """

        cli = ComponentsCli(self)
        cli.setPrompt("components")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_projects(self, arg):
        """projects [arg] : Orchestra Projects management commands.

        no arg -> launch Project management shell.
        arg    -> execute [arg] project command.
        """

        cli = ProjectsCli(self)
        cli.setPrompt("projects")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")

    def do_targets(self, arg):
        """targets [arg] : Orchestra Targets management commands.

        no arg -> launch Target management shell.
        arg    -> execute [arg] target command.
        """

        cli = TargetsCli(self)
        cli.setPrompt("targets")
        arg = str(arg)
        if len(arg) > 0:
            line = cli.precmd(arg)
            cli.onecmd(line)
            cli.postcmd(True, line)
        else:
            cli.cmdloop()
            self.stdout.write("\n")
