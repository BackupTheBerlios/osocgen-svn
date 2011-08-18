#! /usr/bin/python
# -*- coding: utf-8 -*-
#=============================================================================
# Name:     settings.py
# Purpose:  Store session settings and project parameters
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/22
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

"Session settings and project parameters"
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

import os, sys

class Settings(object):
    """Settings class implements a Singleton design pattern to share the same
    state to all instances of this class.
    This class will store the application settings like directory location,
    active component and active project.
    """
    __instance = None
    __do_init = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            cls.__instance.__do_init = False
            return cls.__instance

        cls.__instance = object.__new__(cls, *args, **kwargs)
        cls.__instance.__do_init = True
        return cls.__instance

    def __init__(self):
        if self.__do_init:
            (pathname, _) = os.path.split(sys.argv[0])
            self.__script_dir = os.path.abspath(pathname)
            self.active_project = None
            self.active_component = None
            self.project_component = None
            self.active_target = None

    def _getDir(self, sub_dir=None):
        """Generate directory name based on project base directory.
        
        @param sub_dir: Sub-directory name
        @return: directory full path string 
        """
        if sub_dir:
            return os.path.join(self.__script_dir, sub_dir)
        else:
            return self.__script_dir

    @property
    def base_dir(self):
        """Returns Orchestra base directory."""
        return self._getDir()
    
    @property
    def components_dir(self):
        """Return Orchestra Components base directory."""
        return self._getDir("components")
    
    @property
    def target_dir(self):
        """Return Orchestra Boards base directory."""
        return self._getDir("targets")
    
    @property
    def project_dir(self):
        """Return Orchestra Projects default directory."""
        return self._getDir("projects")
