# -*- coding: utf-8 -*-

import os
import processing

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

from qgis.core import (
    QgsProject,
    QgsField,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol
)

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'mapbiomas_style_dialog_base.ui')
)


class MapBiomasStyleDialog(QDialog, FORM_CLASS):

    def __init__(self, iface, parent=None):
        super(MapBiomasStyleDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = iface

        # Carrega camadas inicialmente
        self.carregar_layers()

        # Atualiza campos quando muda a camada
        self.combo_layer_uso.currentIndexChanged.connect(self.carregar_campos)

        # Atualiza camadas quando novas são adicionadas ao projeto
        QgsProject.instance().layersAdded.connect(self.carregar_layers)

        # Carrega campos iniciais
        self.carregar_campos()

    # -----------------------------
    # CARREGAR CAMADAS
    # -----------------------------
    def carregar_layers(self):
        current_layer = self.combo_layer_uso.currentData()
        self.combo_layer_uso.clear()

        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == layer.VectorLayer:
                self.combo_layer_uso.addItem(layer.name(), layer)

        # Restaura seleção anterior, se existir
        if current_layer:
            index = self.combo_layer_uso.findData(current_layer)
            if index >= 0:
                self.combo_layer_uso.setCurrentIndex(index)

    # -----------------------------
    # CARREGAR CAMPOS
    # -----------------------------
    def carregar_campos(self):
        self.combo_campo.clear()
        layer = self.combo_layer_uso.currentData()
        if not layer:
            return
        for field in layer.fields():
            self.combo_campo.addItem(field.name())
        if self.combo_campo.count() > 0:
            self.combo_campo.setCurrentIndex(0)

    # -----------------------------
    # EXECUTAR
    # -----------------------------
    def executar(self):
        layer = self.combo_layer_uso.currentData()
        campo = self.combo_campo.currentText()

        if not layer:
            return

        if campo == "":
            self.iface.messageBar().pushWarning(
                "MapBiomas Style",
                "Selecione o campo de classe."
            )
            return

        camada_resultado = layer

        # -----------------------------
        # DISSOLVE
        # -----------------------------
        if self.check_dissolve.isChecked():
            params = {
                'INPUT': layer,
                'FIELD': [campo],
                'OUTPUT': 'memory:'
            }
            dissolve = processing.run("native:dissolve", params)
            camada_resultado = dissolve['OUTPUT']
            QgsProject.instance().addMapLayer(camada_resultado)

        # -----------------------------
        # CLASSES MAPBIOMAS
        # -----------------------------
        classes = {
            3: ("Formação Florestal", "#1f8d49"),
            4: ("Formação Savânica", "#7dc975"),
            5: ("Mangue", "#04381d"),
            6: ("Floresta Alagável", "#007785"),
            49: ("Restinga Arbórea", "#02d659"),
            10: ("Formação Campestre", "#d6bc74"),
            11: ("Campo Alagado e Área Pantanosa", "#519799"),
            12: ("Formação Campestre", "#d6bc74"),
            32: ("Apicum", "#fc8114"),
            29: ("Afloramento Rochoso", "#ffaa5f"),
            50: ("Restinga Herbácea", "#ad5100"),
            14: ("Agropecuária", "#ffefc3"),
            15: ("Pastagem", "#edde8e"),
            18: ("Agricultura", "#E974ED"),
            19: ("Lavoura Temporária", "#C27BA0"),
            39: ("Soja", "#f5b3c8"),
            20: ("Cana", "#db7093"),
            40: ("Arroz", "#c71585"),
            62: ("Algodão", "#ff69b4"),
            41: ("Outras Lavouras Temporárias", "#f54ca9"),
            36: ("Lavoura Perene", "#d082de"),
            46: ("Café", "#d68fe2"),
            47: ("Citrus", "#9932cc"),
            35: ("Dendê", "#9065d0"),
            48: ("Outras Lavouras Perenes", "#e6ccff"),
            9: ("Silvicultura", "#7a5900"),
            21: ("Mosaico de Usos", "#ffefc3"),
            22: ("Área não Vegetada", "#d4271e"),
            23: ("Praia, Duna e Areal", "#ffa07a"),
            24: ("Área Urbanizada", "#d4271e"),
            30: ("Mineração", "#9c0027"),
            75: ("Usina Fotovoltaica", "#c12100"),
            25: ("Outras Áreas não Vegetadas", "#db4d4f"),
            26: ("Rio, Lago e Oceano", "#2532e4"),
            33: ("Rio, Lago e Oceano", "#2532e4"),
            31: ("Aquicultura", "#091077"),
            27: ("Não observado", "#ffffff")
        }

        # -----------------------------
        # CAMPO TIPO_USO
        # -----------------------------
        if camada_resultado.fields().indexOf("tipo_uso") == -1:
            camada_resultado.dataProvider().addAttributes([
                QgsField("tipo_uso", QVariant.String)
            ])
            camada_resultado.updateFields()

        idx_tipo = camada_resultado.fields().indexOf("tipo_uso")
        camada_resultado.startEditing()
        for f in camada_resultado.getFeatures():
            valor = f[campo]
            if valor is None:
                continue
            valor = int(valor)
            if valor in classes:
                nome = classes[valor][0]
                camada_resultado.changeAttributeValue(f.id(), idx_tipo, nome)
        camada_resultado.commitChanges()

        # -----------------------------
        # CALCULAR ÁREA
        # -----------------------------
        if self.check_area.isChecked():
            pr = camada_resultado.dataProvider()
            # Adiciona campos de área se não existirem
            for nome_campo, tipo in [("area_ha", QVariant.Double), ("area_km2", QVariant.Double), ("perc_%", QVariant.Double)]:
                if camada_resultado.fields().indexOf(nome_campo) == -1:
                    pr.addAttributes([QgsField(nome_campo, tipo)])
            camada_resultado.updateFields()

            idx_ha = camada_resultado.fields().indexOf("area_ha")
            idx_km2 = camada_resultado.fields().indexOf("area_km2")
            idx_perc = camada_resultado.fields().indexOf("perc_%")

            # Calcula áreas
            camada_resultado.startEditing()
            total_ha = 0
            for f in camada_resultado.getFeatures():
                geom = f.geometry()
                area_m2 = geom.area()
                area_ha = area_m2 / 10000
                area_km2 = area_m2 / 1000000
                camada_resultado.changeAttributeValue(f.id(), idx_ha, round(area_ha, 8))
                camada_resultado.changeAttributeValue(f.id(), idx_km2, round(area_km2, 8))
                total_ha += area_ha
            # Calcula porcentagem
            for f in camada_resultado.getFeatures():
                area = f["area_ha"]
                perc = (area / total_ha) * 100 if total_ha > 0 else 0
                camada_resultado.changeAttributeValue(f.id(), idx_perc, round(perc, 4))
            camada_resultado.commitChanges()

        # -----------------------------
        # SIMBOLOGIA
        # -----------------------------
        categorias = []
        for codigo, (nome, cor) in classes.items():
            simbolo = QgsSymbol.defaultSymbol(camada_resultado.geometryType())
            simbolo.setColor(QColor(cor))
            symbol_layer = simbolo.symbolLayer(0)
            symbol_layer.setStrokeStyle(0)
            categoria = QgsRendererCategory(codigo, simbolo, nome)
            categorias.append(categoria)

        renderer = QgsCategorizedSymbolRenderer(campo, categorias)
        camada_resultado.setRenderer(renderer)
        camada_resultado.triggerRepaint()