#! /usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:     xml.py
# Purpose:  XML file
#
# Author:   Fabrice MOUSSET
#
# Created:  2008/01/16
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

__doc__ = "Defines classes to manage Orchestra XML files."
__version__ = "1.0.0"
__versionTime__ = "16/01/2008"
__author__ = "Fabrice MOUSSET <fabrice.mousset@laposte.net>"

if __name__ == "__main__":
    import os.path as dir
    import sys

    dirname, base = dir.split(dir.dirname(dir.realpath(__file__)))
    sys.path.append(dirname)

import thirdparty.ElementTree as ET

def XMLBeautifier(xml_data):
    """This function make XML output looks better and more readable.
    """
    xml_text = ""
    xml_ident = 0
    for xml_line in xml_data.split('<'):
        xml_line = xml_line.strip()
        if(len(xml_line) > 0):
            if xml_line.endswith("/>"):
                xml_text += ' '*xml_ident + "<" + xml_line + "\n"
            else:
                if(xml_line.startswith('/')):
                    xml_ident -= 4
                    xml_text += ' '*xml_ident + "<" + xml_line + "\n"
                else:
                    xml_text += ' '*xml_ident + "<" + xml_line + "\n"
                    xml_ident += 4

    return xml_text

class ItemBase(object):
    """ This class should help working with elements stored in XML files.
        Eac
    """

    def __init__(self, tag, valid_keys):
        self.__dict__["__text"] = tag
        self.__dict__["__valid_keys"] = valid_keys

    def setKeys(self, valid_keys):
        self.__dict__["__valid_keys"] = valid_keys

    def setAttributs(self, attribs):
        keys = self.__dict__["__valid_keys"]
        for (key,value) in attribs.items():
            if(keys is None) or key in keys:
                self.__dict__[key] = value
            else:
                pass

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            return None

    def __getattr__(self, name):
        name = str(name).lower()
        if name.startswith('_'):
            return None

        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def __setattr__(self, name, value):
        keys = self.__dict__["__valid_keys"]
        if name.startswith('_'):
            return

        if(keys is None):
            self.__dict__[name] = value
        elif name in keys:
            self.__dict__[name] = value

    def __delattr__(self, name):
        pass

    def __str__(self):
        return self.__dict__["__text"]

    def setText(self, value):
        self.__dict__["__text"] = value

    def isItem(self, item):
        return item == self.__dict__["__text"]

    def asXMLTree(self, parent, node_name):
        if(parent is None):
            xml_node =  ET.Element(node_name)
        else:
            xml_node = ET.SubElement(parent, node_name)

        xml_node.text = self.__dict__["__text"]
        for name in self.__dict__:
            if(name.startswith('_') == False):
                xml_node.set(name, str(self.__dict__[name]))

        return xml_node

class NodeBase(object):
    def __init__(self, node_name, valid_keys=(), default_key=None):
        self._valid_keys = valid_keys
        self._default_key = default_key
        self._data = []
        self.__index = 0
        self._node_name = node_name

    def __getitem__(self, idx):
        if isinstance( idx, (int,slice) ):
            return sef._data[index]

        index = self.__getIndexOf(idx)
        if index < 0:
            return ItemBase()
        return sef._data[index]

        return self._data[index]

    def __setitem__(self, idx, value):
        index = self.__getIndexOf(idx)
        if index >= 0:
            self._data[index] = value

    def __delitem__(self, key):
        pass

    def __len__(self):
        return len(self._data)

    def __contains__(self, item):
        if self._default_key is None:
            return item in self._data
        else:
            retval = False
            for data in self._data:
                retval = retval or (item == data[self._default_key])
            return retval

    def __iter__(self):
        self.__index = 0
        return self

    def __str__(self):
        return self._node_name

    def next(self):
        try:
            data = self._data[self.__index]
            self.__index += 1
            return data
        except:
            raise StopIteration

    def __getIndexOf(self, item):
        # Scan _data collection and search match with element name
        for data in self._data:
            if data.isItem(item):
                return self._data.index(data)

        # Verify if item is an integer
        try:
            return int(item)
        except:
            return -1

    def add(self, text=None, attrib={}, **extra):
        attrib = attrib.copy()
        attrib.update(extra)
        item = ItemBase(text, self._valid_keys)
        item.setAttributs(attrib)
        self._data.append(item)

    def remove(self, item):
        if isinstance(item, ItemBase):
            try:
                idx = self._data.index(item)
            except:
                idx = -1
        else:
            idx = self.__getIndexOf(item)
        if idx >= 0:
            del self._data[idx]

    def clear(self):
        self._data = []
        self.__index = 0

    def asXMLTree(self, parent=None):
        # Creation section node
        if(parent is None):
            xml_tree =  ET.Element(self._node_name+'s')
        else:
            xml_tree = ET.SubElement(parent, self._node_name+'s')

        # Append childrens to section node
        for data in self._data:
            data.asXMLTree(xml_tree, self._node_name)

        return xml_tree

class XmlFileBase(object):
    description = None
    xml_basename = "filebase"

    def __create_node(self, node_name, attribs, xml_root):
        node = NodeBase(node_name[:-1], attribs)
        if xml_root is not None:
            nodes = xml_root.find(node_name)
            if nodes is not None:
                for el in nodes:
                    node.add(el.text, el.attrib)

        self.__dict__[node_name] = node


    def __init__(self, nodes, attribs, filename=None, xml_data=None):

        keys = nodes.keys()
        keys.append(attribs.keys())
        keys.append(("_nodes","_attribs","_keys","_basekeys"))

        self.__dict__["_nodes"] = nodes
        self.__dict__["_attribs"] = attribs
        self.__dict__["_basekeys"] = keys
        keys.append("description")
        self.__dict__["_keys"] = keys

        for (name, value) in self._attribs.iteritems():
            self.__dict__[name] = value

        try:
            xml_root = ET.parse(filename)
        except:
            xml_root = None

        if xml_root is None:
            try:
                xml_root = ET.ElementTree(ET.fromstring(xml_data))
            except:
                xml_root = None

        for (name,attrib) in nodes.iteritems():
            self.__create_node(name, attrib, xml_root)

        if xml_root is not None:
            el = xml_root.getroot()
            for (name, value) in el.attrib.items():
                self.__dict__[name] = value

            el = xml_root.find("description")
            if(el != None):
                self.description = str(el.text)

    def __setattr__(self, name, value):
        # XML nodes modifications are not allowed !!!
        if(self.__dict__.has_key("_basekeys")):
            if name in self.__dict__["_nodes"].keys():
                pass
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value


    def __delattr__(self, name):
        # Component base elements suppression canceled
        if name in self._basekeys:
            pass

    def asXMLTree(self):
        xml_tree = ET.Element(self.xml_basename)
        for attr in self._attribs.keys():
            xml_tree.set(attr, self.__dict__[attr])

        if self.description is not None:
            description = ET.SubElement(xml_tree, "description")
            description.text = str(self.description)

        for node_name in self._nodes.iterkeys():
            self.__dict__[node_name].asXMLTree(xml_tree)

        return xml_tree

    def asXML(self, encoding="utf-8"):
        xml_tree = self.asXMLTree()
        xml_string = ET.tostring(xml_tree, encoding)
        return XMLBeautifier(xml_string)

    def __str__(self):
        return self.asXML()
