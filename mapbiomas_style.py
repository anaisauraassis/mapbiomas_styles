# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

import os

from .mapbiomas_style_dialog import MapBiomasStyleDialog


class MapBiomasStyle:

    def __init__(self, iface):

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.actions = []
        self.menu = 'MapBiomas Style'

        # cria dialog
        self.dlg = MapBiomasStyleDialog(self.iface)


    def tr(self, message):

        return QCoreApplication.translate(
            'MapBiomasStyle',
            message
        )


    def add_action(
        self,
        icon_path,
        text,
        callback,
        parent=None
    ):

        icon = QIcon(icon_path)

        action = QAction(
            icon,
            text,
            parent
        )

        action.triggered.connect(callback)

        # MENU
        self.iface.addPluginToMenu(
            self.menu,
            action
        )

        # TOOLBAR (ÍCONE)
        self.iface.addToolBarIcon(
            action
        )

        self.actions.append(action)

        return action


    def initGui(self):

        # CAMINHO REAL DO ÍCONE
        icon_path = os.path.join(
            self.plugin_dir,
            'icon.png'
        )

        self.add_action(
            icon_path,
            text=self.tr('MapBiomas Style'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )


    def unload(self):

        for action in self.actions:

            self.iface.removePluginMenu(
                self.menu,
                action
            )

            self.iface.removeToolBarIcon(
                action
            )


    def run(self):

        self.dlg.show()

        result = self.dlg.exec_()

        if result:
            self.dlg.executar()