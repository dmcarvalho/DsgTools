# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2016-09-14
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Luiz Andrade - Cartographic Engineer @ Brazilian Army
        email                : luiz.claudio@dsg.eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import QgsMessageLog, QgsVectorLayer, QgsMapLayerRegistry, QgsGeometry, QgsVectorDataProvider, QgsFeatureRequest, QgsExpression, QgsFeature
from DsgTools.ValidationTools.ValidationProcesses.validationProcess import ValidationProcess
import processing, binascii

class SnapGeometriesProcess(ValidationProcess):
    def __init__(self, postgisDb, codelist):
        super(self.__class__,self).__init__(postgisDb, codelist)
        self.parameters = {'Snap': 1.0, 'MinArea':0.001}
        
    def postProcess(self):
        '''
        Gets the process that should be execute after this one
        '''
        return 'ForceValidityGeometriesProcess'

    def runProcessinAlg(self, cl):
        alg = 'grass7:v.clean.advanced'
        
        #creating vector layer
        input = QgsVectorLayer(self.abstractDb.getURI(cl, True).uri(), cl, "postgres")
        crs = input.crs()
        epsg = self.abstractDb.findEPSG()
        crs.createFromId(epsg)
        input.setCrs(crs)
        
        #Adding to registry
        QgsMapLayerRegistry.instance().addMapLayer(input)
        
        #setting tools
        tools = 'snap'
        threshold = self.parameters['Snap']
        minArea = self.parameters['MinArea']
        snap = -1

        #getting table extent (bounding box)
        tableSchema, tableName = self.abstractDb.getTableSchema(cl)        
        (xmin, xmax, ymin, ymax) = self.abstractDb.getTableExtent(tableSchema, tableName)
        extent = '{0},{1},{2},{3}'.format(xmin, xmax, ymin, ymax)
        
        ret = processing.runalg(alg, input, tools, threshold, extent, snap, minArea, None, None)

        #updating original layer
        outputLayer = processing.getObject(ret['output'])
        self.updateOriginalLayer(input, outputLayer)
          
        #getting error flags
        errorLayer = processing.getObject(ret['error'])
        #removing from registry
        QgsMapLayerRegistry.instance().removeMapLayer(input.id())
        return self.getProcessingErrors(errorLayer)

    def updateOriginalLayer(self, pgInputLyr, grassOutputLyr):
        '''
        Updates the original layer using the grass output layer
        pgInputLyr: postgis input layer
        grassOutputLyr: grass output layer
        '''
        provider = pgInputLyr.dataProvider()
        pgInputLyr.startEditing()
        addList = []
        for feature in pgInputLyr.getFeatures():
            id = feature['id']
            grassFeats = []
            for gf in grassOutputLyr.dataProvider().getFeatures(QgsFeatureRequest(QgsExpression("id=%d"%id))):
                grassFeats.append(gf)
            for i in range(len(grassFeats)):
                if i == 0:
                    newGeom = grassFeats[i].geometry()
                    newGeom.convertToMultiType()
                    feature.setGeometry(newGeom)
                    pgInputLyr.updateFeature(feature)
                else:
                    newFeat = QgsFeature(feature)
                    newGeom = grassFeats[i].geometry()
                    newGeom.convertToMultiType()
                    newFeat.setGeometry(newGeom)
                    idx = newFeat.fieldNameIndex('id')
                    newFeat.setAttribute(idx,provider.defaultValue(idx))                    
                    addList.append(newFeat)
        pgInputLyr.addFeatures(addList,True)
        pgInputLyr.commitChanges()
    
    def getProcessingErrors(self, layer):
        recordList = []
        for feature in layer.getFeatures():
            recordList.append((feature.id(), binascii.hexlify(feature.geometry().asWkb())))
        return recordList
        
    def execute(self):
        #abstract method. MUST be reimplemented.
        QgsMessageLog.logMessage('Starting '+self.getName()+'Process.\n', "DSG Tools Plugin", QgsMessageLog.CRITICAL)
        try:
            self.setStatus('Running', 3) #now I'm running!
            self.abstractDb.deleteProcessFlags(self.getName()) #erase previous flags
            classesWithGeom = self.abstractDb.listClassesWithElementsFromDatabase()
            if classesWithGeom.__len__() == 0:
                self.setStatus('Empty database!\n', 1) #Finished
                QgsMessageLog.logMessage('Empty database!\n', "DSG Tools Plugin", QgsMessageLog.CRITICAL)                
                return
            for cl in classesWithGeom:
                if cl[-1]  in ['a', 'l']:
                    print cl
                    result = self.runProcessinAlg(cl)
                    if len(result) > 0:
                        recordList = []
                        for tupple in result:
                            recordList.append((cl,tupple[0],'Snapping error.',tupple[1]))
                            self.addClassesToBeDisplayedList(cl) 
                        numberOfProblems = self.addFlag(recordList)
                        self.setStatus('{} feature(s) of class '+cl+' with snapping errors. Check flags.\n' .format(numberOfProblems), 4) #Finished with flags
                        QgsMessageLog.logMessage('{} feature(s) of class '+cl+' with snapping errors. Check flags.\n' .format(numberOfProblems), "DSG Tools Plugin", QgsMessageLog.CRITICAL)
                    else:
                        self.setStatus('There are no snapping errors on '+cl+'.\n', 1) #Finished
                        QgsMessageLog.logMessage('There are no snapping errors on '+cl+'.\n', "DSG Tools Plugin", QgsMessageLog.CRITICAL)
            return 1
        except Exception as e:
            QgsMessageLog.logMessage(str(e.args[0]), "DSG Tools Plugin", QgsMessageLog.CRITICAL)
            self.finishedWithError()
            return 0
