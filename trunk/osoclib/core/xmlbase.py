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
    """This function make XML output looks better and more humman readable.
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

def initialize_node(node, node_name, xml_root, subnodes=None):
    """This routine creates nodes/attributes with initialization.
    
        Attributes:
         * node:      Data node
         * node_name: XLM base node name
         * xml_root:  XML initialization datas
         * subnodes:  Sub elements
    """

    if xml_root is not None:
        xml_nodes = xml_root.find(node_name)
        if xml_nodes is not None:
            for el in xml_nodes:
                subelement = node.add(el.text, el.attrib)

                if subnodes is not None:
                    for (subnode_name, subnode_attrib) in subnodes.iteritems():
                        if(isinstance(subnode_attrib, dict)):
                            if subnode_attrib.has_key("subnodes"):
                                initialize_node(subelement, subnode_name, el, subnode_attrib["subnodes"])
                            else:
                                initialize_node(subelement, subnode_name, el, None)
                        else:
                            initialize_node(subelement, subnode_name, el, None)
    
    return node

def create_node(node_name, attribs, xml_root, subnodes=None):
    """This routine creates nodes/attributes with initialization.
    
        Attributes:
         * node_name: XLM base node name
         * attribs:   Node valid attributes name
         * xml_root:  XML initialization datas
         * subnodes:  Sub elements
    """
    node = NodeBase(node_name[:-1], attribs)
    
    if subnodes is not None:
        node.setSubNobes(subnodes)

    return initialize_node(node, node_name, xml_root, subnodes)

class ItemBase(object):
    """ This class should help working with elements stored in XML files.
        
        Direct acces to each attribut is possible via dictionary or as object attribut.
        Attribut names are caseless.
        
        Attributes:
            tag           Node description
            valid_keys    Valid attributes
    """

    def __init__(self, tag, valid_keys=None):
        self.__dict__["__text"] = tag
        self.__dict__["__valid_keys"] = valid_keys
#        self.__dict__["__sub_nodes"] = {}

    def setKeys(self, valid_keys):
        self.__dict__["__valid_keys"] = valid_keys

    def setAttributs(self, attribs):
        keys = self.__dict__["__valid_keys"]
        for (key,value) in attribs.items():
            if(keys is None) or key in keys:
                self.__dict__[key] = value
            else:
                pass

    # __getattribute__ is called for each class attribute access.
    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            return None

    # __getattr__ is called only for attributes that can't be found.
    def __getattr__(self, name):
        name = str(name).lower()
        
        # No direct access to private members ;-)
        if name.startswith('_'):
            return None

        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def __setattr__(self, name, value):
        keys = self.__dict__["__valid_keys"]

        # No direct access to private members ;-)
        if name.startswith('_'):
            return

        if(keys is None):
            self.__dict__[name] = value
        elif name in keys:
            self.__dict__[name] = value

    # We don't want to remove attributes
    def __delattr__(self, name):
        pass

    def __str__(self):
        return self.__dict__["__text"]

    def setText(self, value):
        self.__dict__["__text"] = value

    def isItem(self, item):
        if isinstance(item, basestring):
            if self.__dict__.has_key("name"):
                return item.lower() == self.__dict__["name"].lower()
            return item.lower() == self.__dict__["__text"].lower()
        
        return item == self

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
    """ This class should help working with elements stored in XML files.
        Direct acces to each attribut is possible via dictionary or as object attribut.
        Attribut names are caseless.
        
        Attributes:
            node_name    Node base name, subnodes
            valid_keys   Valid attributes
            sub_nodes    Sub-nodes names and attributes
    """

    def __init__(self, node_name, valid_keys=(), default_key=None):
        self._valid_keys = valid_keys
        self._default_key = default_key
        self._data = []
        self.__index = 0
        self._node_name = node_name
        self._sub_nodes = None

    def __getitem__(self, idx):
        index = self.__getIndexOf(idx)
        if index < 0:
            return ItemBase()
        return sef._data[index][0]

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
            for element in self._data:
                data = element[0]
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
            return data[0]
        except:
            raise StopIteration

    def __getIndexOf(self, item):
        # Scan _data collection and search match with element name
        for data in self._data:
            if data[0].isItem(item):
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

        sub_nodes = {}
        if self._sub_nodes is not None:
            for (node_name, node_attrib) in self._sub_nodes.iteritems():
                if(isinstance(node_attrib, dict)):
                    if node_attrib.has_key("subnodes"):
                        node = create_node(node_name, node_attrib["attribs"], None, node_attrib["subnodes"],)
                    else:
                        node = create_node(node_name, node_attrib["attribs"], None)
                else:
                    node = create_node(node_name, node_attrib, None)
                
                sub_nodes[node_name] = node
        
        element = item, sub_nodes        
        self._data.append(element)
        
        return element

    def remove(self, item):
        idx = self.__getIndexOf(item)
        if idx >= 0:
            del self._data[idx]
            return True
        
        return False

    def hasElement(self, item):
        return self.__getIndexOf(item) >= 0
    
    def getElement(self, item):
        idx = self.__getIndexOf(item)
        if idx >= 0:
            return self._data[idx]    
        return None
    
    
    def clear(self):
        self._data = []
        self.__index = 0

    def setSubNobes(self, sub_nodes):
        self._sub_nodes = sub_nodes
        
    def asXML(self, encoding="utf-8"):
        xml_tree = self.asXMLTree()
        xml_string = ET.tostring(xml_tree, encoding)
        return XMLBeautifier(xml_string)

    def asXMLTree(self, parent=None):
        # Creation section node
        if(parent is None):
            xml_tree =  ET.Element(self._node_name+'s')
        else:
            xml_tree = ET.SubElement(parent, self._node_name+'s')

        # Append childrens to section node
        for (item, sub_nodes) in self._data:
            data = item.asXMLTree(xml_tree, self._node_name)
            # Append sub-nodes to XML Tree
            for (sub_node_name, sub_node_element) in sub_nodes.iteritems():
                sub_node_element.asXMLTree(data)

        return xml_tree

class XmlFileBase(object):
    """This class will help to managed each XML files used for Orchestra project.
        
        Attributes:
            nodes:    dictionnary which describe each nodes and sub-nodes
            attribs:  base node attributes
            filename: XML file name, used to initialise the class members
            xml_data: XML string, used to initialise the class members
    """
    description = None
    xml_basename = "filebase"

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

        for (node_name, node_attrib) in nodes.iteritems():
            if(isinstance(node_attrib, dict)):
                if node_attrib.has_key("subnodes"):
                    node = create_node(node_name, node_attrib["attribs"], xml_root, node_attrib["subnodes"],)
                else:
                    node = create_node(node_name, node_attrib["attribs"], xml_root)
            else:
                node = create_node(node_name, node_attrib, xml_root)
                
            self.__dict__[node_name] = node

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
