#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     cli.py
# Purpose:  Basic Command Line Interface for Orchestra elements
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/17
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

"Basic Command Line Interface"
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import cmd, re, os

class BaseCli(cmd.Cmd):
    case_insensitive = True
    comment_marks = '#*'
    exclude_from_history = []
    multiline_commands = []
    continuation_prompt = '> '
    shortcuts = {'?': 'help', '!': 'shell', '@': 'load'}
    terminators = '\n'
    multiline_terminator = '.'
    default_extension = 'txt'

    def __init__(self, parent=None, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs)
        self._hist = []
        self.parent=parent
        if parent is None:
            self.setPrompt("orchestra")
        else:
            self.stdin = parent.stdin
            self.stdout = parent.stdout
            self.use_rawinput = parent.use_rawinput

    def finishStatement(self, firstline):
        inp = firstline
        lines = []
        while not self.statementHasEnded(inp):
            lines.append(inp)
            inp = self.pseudo_raw_input(self.continuation_prompt)
        return '\n'.join(lines)

    def write(self, message):
        self.stdout.write(message)

    def readline(self):
        return self.stdin.readline()

    def pseudo_raw_input(self, prompt):
        """copied from cmd's cmdloop; like raw_input, but accounts for changed stdin, stdout"""

        if self.use_rawinput:
            try:
                line = raw_input(prompt)
            except EOFError:
                line = 'EOF'
        else:
            self.stdout.write(prompt)
            self.stdout.flush()
            line = self.stdin.readline()
            if not len(line):
                line = 'EOF'
            else:
                if line[-1] == '\n': # this was always true in Cmd
                    line = line[:-1]
        return line

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        # An almost perfect copy from Cmd; however, the pseudo_raw_input portion
        # has been split out so that it can be called separately

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    line = self.pseudo_raw_input(self.prompt)
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def statementHasEnded(self, line):
        return line == self.multiline_terminator or line[-3:] == 'EOF'

    def clean(self, s):
        """cleans up a string"""
        if self.case_insensitive:
            return s.strip().lower()
        return s.strip()

    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        shortcut = self.shortcuts.get(line[0])
        if shortcut and hasattr(self, 'do_%s' % shortcut):
            line = '%s %s' % (shortcut, line[1:])
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        command, arg = line[:i], line[i:].strip().strip(self.terminators)
        return command, arg, line

    def onecmd(self, line):
        """Interpret the argument as though it had been typed in response
        to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        try:
            (command, args) = line.split(None,1)
        except ValueError:
            (command, args) = line, ''

        try:
            (sub_cmd, end_cmd) = command.split('.',1)
            command = sub_cmd
            args = ' '.join([end_cmd, args])
        except:
            pass

        if self.case_insensitive:
            command = command.lower()
        
        if command in self.multiline_commands and len(args) > 0:
            args = self.finishStatement(args)
        statement = ' '.join([command, args])
        
        stop = cmd.Cmd.onecmd(self, statement)
        try:
            command = statement.split(None,1)[0].lower()
            if command not in self.exclude_from_history:
                self.history.append(statement)
        finally:
            return stop

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        #print "Exiting..."


    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted.
        """

        # Remove comments lines
        try:
            if str(line)[0] in str(self.comment_marks):
                return ""
        except:
            return ""

        if line:
            self._hist += [ line.strip() ]
        return line

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """

        self.stdout.write("*** Unknown Syntax : %s (type help for a list of valid command\n"%line)

        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with '!'."""
        os.system(arg)

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def do_quit(self, arg):
        """Exits from the command line interpreter.\n"""
        return True

    do_exit = do_quit

    def do_load(self, fname=None):
        """Runs command(s) from a file.
           load <filename> used <filename> as standard input execute commands stored in.
        """
        if fname is None:
            fname = self.default_filename
        keepstate = Statekeeper(self, ('stdin','use_rawinput','prompt','base_prompt', 'continuation_prompt'))
        try:
            self.stdin = open(fname, 'r')
        except IOError, e:
            try:
                self.stdin = open('%s.%s' % (fname, self.default_extension), 'r')
            except IOError:
                print 'Problem opening file %s: \n%s' % (fname, e)
                keepstate.restore()
                return
        self.use_rawinput = False
        self.prompt = self.continuation_prompt = ''
        self.cmdloop()
        self.stdin.close()
        keepstate.restore()
        self.lastcmd = ''

    def do_EOF(self, args):
        """Exit on system end of file character.\n"""
        return self.do_exit(args)

    do_eof = do_EOF

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    # Property to manage active projet
    def setPrompt(self, prompt):
        """Update command line prompt and continuation prompt."""
        prompt = str(prompt).strip()
        if self.parent is None:
            self.base_prompt = prompt
        else:
            self.base_prompt = self.parent.base_prompt+"."+prompt
        self.prompt = self.base_prompt+"> "
        self.continuation_prompt = " "*len(self.base_prompt)+"> "

class Statekeeper(object):
    def __init__(self, obj, attribs):
        self.obj = obj
        self.attrib_names = attribs
        self.attribs = {}
        self.save()
    def save(self):
        for attrib in self.attrib_names:
            self.attribs[attrib] = getattr(self.obj, attrib)
    def restore(self):
        for attrib in self.attrib_names:
            setattr(self.obj, attrib, self.attribs[attrib])
