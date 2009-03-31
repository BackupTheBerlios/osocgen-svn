#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     zipextended.py
# Purpose:  ZIP files manipulation routines
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/02/06
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

__doc__ = "ZIP files manipulations routines"
__version__ = "1.0.0"
__versionTime__ = "xx/xx/xxxx"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

from zipfile import ZipFile, is_zipfile, ZipInfo, ZIP_DEFLATED
import os.path as ospath
import os
import glob
import time
import re

# Try to include cStringIO if avialable, is quiet faster than StringIO
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def normDirname(dirname):
    dirname = dirname.replace("\\", "/")
    if dirname.startswith("/"):
        dirname = dirname[1:]
    if len(dirname):
        if not dirname.endswith('/'):
            dirname += '/'

    return dirname

def is_matching_patterns(patterns, item):
    for pattern in patterns:
        if pattern.match(item.upper()):
            return True
    return False

# pylint: disable-msg=W0622
def filter(items, patterns):
    """
    Retourne deux sous-listes de la liste-fichiers LST :
       - la première est la liste qui respecte la liste PATTERNS
       - la deuxième est la liste qui ne respecte pas la liste PATTERNS
    filter remplace fnmatch, car sous Windows fnmatch se plante avec '*.*' et les fichiers '*.'
    """

    re_patterns = [re.compile(pattern.upper()) for pattern in patterns]
    result = [item for item in items
              if is_matching_patterns(re_patterns, item)
              ]

    # pylint: disable-msg=W0631
    antiresult = [item for item in items
                        if not item in result]
    result.sort()
    antiresult.sort()
    return(result,antiresult)

class _ZipString(ZipFile):
    def __init__(self, zip_string):
        buffer = StringIO()
        if zip_string:
            if is_zipfile(zip_string):
                fp = open(zip_string, "rb")
                while 1:
                    data = fp.read(1024 * 8)
                    if not data:
                        break
                    buffer.write(data)
                fp.close()
            else:
                buffer.write(zip_string)

        ZipFile.__init__(self, buffer, 'a', compression=ZIP_DEFLATED)

class ExtendedZipFile(ZipFile):
    def createDirectory(self, dirname):
        dirname = normDirname(dirname)
        if len(dirname):
            zdir = ZipInfo(dirname, time.localtime()[0:6])
            self.writestr(zdir,'')

    def addDirectory(self, path, zippath=''):
        def _zipdirectory(zf, path, zippath):
            for fname in glob.glob(path+'\\*'):
                filename = ospath.join(zippath,ospath.basename(fname))
                if ospath.isdir(fname):
                    self.createDirectory(filename)
                    _zipdirectory(zf, fname, filename)
                else:
                    zf.write(fname, filename)

        _zipdirectory(self, path, normDirname(zippath))

    def unzip(self, destination = '', pattern='*'):
        if destination == '':
            destination = os.getcwd()  ## on dezippe dans le repertoire locale

        for zfile in self.namelist():  ## On parcourt l'ensemble des fichiers de l'archive
            filename = ospath.join(destination, zfile)
            if zfile.endswith('/'):   ## S'il s'agit d'un repertoire, on se contente de creer le dossier
                try:
                    os.makedirs(filename)
                except:
                    pass
            else:
                data = self.read(zfile)                 ## lecture du fichier compresse
                fp = open(filename, "wb")               ## creation en local du nouveau fichier
                fp.write(data)                          ## ajout des donnees du fichier compresse dans le fichier local
                fp.close()

    def removeDirectory(self, dirname):
        if not self.mode in ("w", "a"):
            return

        patterns = []
        if isinstance(dirname, list):
            for pattern in dirname:
                if isinstance(pattern, basestring):
                    pattern = normDirname(pattern)
                    if pattern:
                        pattern += '*'
                    else:
                        pattern = '*'
                patterns.append(pattern)
        else:
            pattern = normDirname(dirname)
            if pattern:
                pattern += '*'
            else:
                pattern = '*'
            patterns.append(pattern)

        self.removeFile(patterns)

    def removeFile(self, filepatterns):
        if not self.mode in ("w", "a"):
            return

        if not isinstance(filepatterns, list):
            filepatterns = [filepatterns]

        (lst,antilst) = filter(self.namelist(), filepatterns)

        # No file to remove, we can leave now
        if not lst:
            return

        zramfile = _ZipString("")
        self.flush()
        for item in antilst:
            item = item.replace("\\", '/')
            info = self.getinfo(item)
            data = self.read(item)
            zramfile.writestr(info, data)

        zramfile.flush()

        if isinstance(self.fp, file):
            self.fp.close()
            self.fp = open(self.filename, "wb")
            zramfile.fp.seek(0,0)
            while 1:
                data = zramfile.fp.read(1024 * 8)
                if not data:
                    break
                self.fp.write(data)

            self.fp.close()
            modeDict = {'r' : 'rb', 'w': 'wb', 'a' : 'r+b'}
            self.fp = open(self.filename, modeDict[self.mode])
            zramfile.close()
        else:
            self.fp.close()
            self.fp = zramfile.fp
            zramfile.fp = None

        self._reload()

    def update(self, filename, file):
        if not self.mode in ("w", "a"):
            return

        if filename in self.namelist():
            self.removeFile(filename)
        self.write(file, filename, ZIP_DEFLATED)

    def updatestr(self, filename, bytes):
        if not self.mode in ("w", "a"):
            return

        if filename in self.namelist():
            self.removeFile(filename)
        zinfo = ZipInfo(filename, time.localtime()[0:6])
        self.writestr(zinfo, bytes)

class ZipString(ExtendedZipFile):
    def __init__(self, zip_string):
        iobuffer = StringIO()
        if zip_string:
            if is_zipfile(zip_string):
                fp = open(zip_string, "rb")
                while 1:
                    data = fp.read(1024 * 8)
                    if not data:
                        break
                    iobuffer.write(data)
                fp.close()
            else:
                iobuffer.write(zip_string)

        ExtendedZipFile.__init__(self, iobuffer, 'a', compression=ZIP_DEFLATED)

    def saveAs(self, filename):
        self.flush()
        if self.fp is None:
            return

        fp = open(filename, "w+b")
        self.fp.seek(0,0)
        while 1:
            buf = self.fp.read(1024 * 8)
            if not buf:
                break
            fp.write(buf)
        fp.close()
        self._reload()



if __name__ == "__main__":
    fpr = open("../../temp/syscon.zip", "rb")
    fpw = open("../../temp/syscon_test.zip", "wb")
    fpw.write(fpr.read())
    fpw.close()
    fpr.close()

    zfile = ExtendedZipFile("../../temp/syscon_test.zip",'a', compression=ZIP_DEFLATED)
    zramfile = ZipString("../../temp/syscon.zip")
    zramfile.printdir()
    print ' -=-'*20
    zfile.printdir()
    print '-'*80
    zramfile.createDirectory("/test")
    zfile.createDirectory("\\test")
    #zfile.printdir()
    #print '-'*80
    zramfile.write("../../temp/imx_wrapper.xml", "test/imx_wrapper.xml")
    zfile.write("../../temp/imx_wrapper.xml", "test/imx_wrapper.xml")
    zramfile.printdir()
    print ' -=-'*20
    zfile.printdir()
    print '-'*80
    zramfile.removeDirectory("test")
    zramfile.printdir()

    zramfile.saveAs("../../temp/test.zip")
    zramfile.close()

    zfile.removeDirectory(["hdl"])
    zfile.write("../../script.txt", "script.txt")
    donnees = """
--------------------------------------------------------------------------------
Ceci est le message que moi, pauvre terrien vais placer dans ce fichier de
test pour voir si la mise à jour d'un fichier dans une archive est possible :)
--------------------------------------------------------------------------------
    """
    zfile.updatestr("script.txt", donnees)
    zfile.printdir()
    zfile.close()
