import typing

from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import Qt

from hivemind_ui.qt_util import VBox, NavButton, register_xml
from hivemind_ui import app, config, errors


class ConfigTableRow:
    def __init__(self, key, typ, value):
        self.key_item = QtWidgets.QTableWidgetItem(key)
        self.type_item = QtWidgets.QTableWidgetItem(typ.__name__)
        self.value_item = QtWidgets.QTableWidgetItem(str(value))
        self.items = [self.key_item, self.type_item, self.value_item]
        [item.setTextAlignment(Qt.AlignCenter) for item in self.items]
        self.key_item.setFlags(Qt.ItemIsSelectable)  # This disables it...?
        self.type_item.setFlags(Qt.ItemIsSelectable)

    def appendTo(self, li: QtWidgets.QTableWidget):
        row = li.rowCount()
        li.insertRow(row)
        for col, item in enumerate(self.items):
            li.setItem(row, col, item)
            

@register_xml('ConfigPage')
class ConfigPage(VBox):
    search_bar: QtWidgets.QLineEdit
    li: QtWidgets.QTableWidget

    def __init__(self):
        super().__init__()
        self.load_xml('ConfigPage.xml')
        
        self.li.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem('key'))
        self.li.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem('type'))
        self.li.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem('value'))
        self.li.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.li.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.li.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.li.horizontalHeader().setMinimumSectionSize(250)

        self.li.verticalHeader().hide()

        self.populate('')
        
        self.search_bar.textChanged.connect(self.edit_search, type=Qt.QueuedConnection)
        self.li.dataChanged = self.data_changed

    def data_changed(self, top_left: QtCore.QModelIndex, bottom_right: QtCore.QModelIndex, roles: typing.Any):
        row = top_left.row()
        key = self.li.item(row, 0).text()
        val = self.li.item(row, 2).text()
        try:
            config.set_config(key, val)
        except errors.HivemindError as e:
            self.li.item(row, 2).setText(str(config.get_config(key)))
            app.display_error(e)

    def edit_search(self, ev: QtCore.QEvent):
        self.populate(self.search_bar.text())

    def populate(self, k_search: str):
        self.li.setRowCount(0)
        for k, t, v in config.typed_items():
            if k_search in k:
                row = ConfigTableRow(k, t, v)
                row.appendTo(self.li)


@register_xml('ConfigNavButton')
class ConfigNavButton(NavButton):
    text = 'configure'
    panel_class = ConfigPage
