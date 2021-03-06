"""
2019.02.05抽离typeWidget
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from .graph import Graph


class TypeWidget(QtWidgets.QWidget):
    TypeShowChanged = QtCore.pyqtSignal()

    def __init__(self, graph: Graph, parent=None):
        super(TypeWidget, self).__init__(parent)
        self.graph = graph
        self.initWidget()

    def initWidget(self):
        vlayout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        btnShowDown = QtWidgets.QPushButton("显示下行")
        btnShowDown.clicked.connect(lambda: self._set_dir_show(True, True))
        btnShowUp = QtWidgets.QPushButton("显示上行")
        btnShowUp.clicked.connect(lambda: self._set_dir_show(False, True))
        hlayout.addWidget(btnShowDown)
        hlayout.addWidget(btnShowUp)
        vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnNoDown = QtWidgets.QPushButton("隐藏下行")
        btnNoDown.clicked.connect(lambda: self._set_dir_show(True, False))
        btnNoUp = QtWidgets.QPushButton("隐藏上行")
        btnNoUp.clicked.connect(lambda: self._set_dir_show(False, False))
        hlayout.addWidget(btnNoDown)
        hlayout.addWidget(btnNoUp)
        vlayout.addLayout(hlayout)

        listWidget = QtWidgets.QListWidget()
        self.listWidget = listWidget
        listWidget.setSelectionMode(listWidget.MultiSelection)

        self._setTypeList()

        vlayout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton("确定")
        btnCancel = QtWidgets.QPushButton("还原")

        btnOk.clicked.connect(self._apply_type_show)
        btnCancel.clicked.connect(self._setTypeList)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        vlayout.addLayout(hlayout)
        self.setLayout(vlayout)

    def _setTypeList(self):
        """
        影响不大，暂时保留
        """
        listWidget = self.listWidget
        listWidget.clear()
        for type in self.graph.typeList:
            item = QtWidgets.QListWidgetItem(type)
            listWidget.addItem(item)
            if type not in self.graph.UIConfigData()["not_show_types"]:
                item.setSelected(True)

    # slots
    def _set_dir_show(self, down, show):
        self.graph.setDirShow(down, show)
        self.TypeShowChanged.emit()

    def _apply_type_show(self):
        listWidget = self.listWidget
        not_show = []
        for i in range(listWidget.count()):
            item: QtWidgets.QListWidgetItem = listWidget.item(i)
            if not item.isSelected():
                not_show.append(item.text())

        self.graph.setNotShowTypes(not_show)
        self.TypeShowChanged.emit()
