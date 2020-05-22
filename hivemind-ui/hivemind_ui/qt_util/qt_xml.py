import xml.etree.ElementTree as xml
from typing import Optional, Dict, List, Any

from PySide2 import QtWidgets, QtWebEngineWidgets
from PySide2.QtCore import QObject, Qt

import hivemind_ui.util
import hivemind_ui.qt_util.base


# I was frustrated with the QT markup loaders so I wrote my own


widgets = {
    k: v
    for k, v in QtWidgets.__dict__.items()
    if not k.startswith('_')
}
widgets.update({
    k: v
    for k, v in QtWebEngineWidgets.__dict__.items()
    if not k.startswith('_')
})

qt_vals = Qt.__dict__


def register(name: str):
    def wrapper(cls):
        widgets[name] = cls
        return cls
    return wrapper


class XmlComponent(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()

    def load_xml(self, fpath: str):
        load_into_object(hivemind_ui.util.get_resource(fpath), self)


def load(fpath: str, parent: Optional[QObject] = None):
    document = xml.parse(fpath)
    node = build_node(document.getroot(), parent=parent)
    return node


def load_into_object(fpath: str, obj: XmlComponent):
    document = xml.parse(fpath)
    node_xml = document.getroot()
    
    attrib = node_xml.attrib
    _get_positional(attrib)  # discarded
    ext_properties = {k: attrib.pop(k) for k in {'name', 'stretch'} if k in attrib}
    setters = {k: attrib.pop(k) for k in set(attrib.keys()) if k.startswith('set')}
    
    _fmt_node(obj, ext_properties, setters)
    
    names = {}
    for child_xml in node_xml:
        build_node(child_xml, parent=obj, names=names)
    for name, node in names.items():
        setattr(obj, name, node)


def build_node(
        node_xml: xml.Element, 
        parent: Optional[QObject] = None, 
        names: Optional[Dict] = None,
) -> QObject:
    attrib = node_xml.attrib
    positional = _get_positional(attrib)
    ext_properties = {k: attrib.pop(k) for k in {'name', 'stretch'} if k in attrib}
    setters = {k: attrib.pop(k) for k in set(attrib.keys()) if k.startswith('set')}

    node = widgets[node_xml.tag](*positional, **attrib)

    _fmt_node(node, ext_properties, setters, parent=parent, names=names)
    
    for child_xml in node_xml:
        build_node(child_xml, parent=node, names=names)

    return node


def _fmt_node(
        node: QtWidgets.QWidget,
        ext_properties: Dict,
        setters: Dict,
        parent: Optional[QtWidgets.QWidget] = None,
        names: Optional[Dict] = None,
):
    if 'name' in ext_properties:
        node.setObjectName(ext_properties['name'])
        if names is not None:
            names[ext_properties['name']] = node

    for setter, value in setters.items():
        getattr(node, setter)(*_get_value(value))
        
    if parent is not None:
        add_args = {}
        if 'stretch' in ext_properties:
            add_args['stretch'] = int(ext_properties['stretch'])
        parent.addWidget(node, **add_args)


def _get_positional(attrib: Dict) -> List:
    res = []
    test = 'arg0'
    idx = 0
    while test in attrib:
        res.append(attrib.pop(test))
        idx += 1
        test = 'arg' + str(idx)
    return res


def _get_value(val: str) -> Any:
    if val.startswith('$(') and val.endswith(')'):
        return eval(val[2:-1])
    if val.startswith('@'):
        return qt_vals[val[1:]],
    if val == 'True':
        return True,
    if val == 'False':
        return False,
    try:
        return int(val),
    except ValueError:
        pass
    try:
        return float(val),
    except ValueError:
        pass
    return val,
