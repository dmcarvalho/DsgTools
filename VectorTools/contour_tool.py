# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                             -------------------
        begin                : 2015-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Brazilian Army - Geographic Service Bureau
        email                : suporte.dsgtools@dsg.eb.mil.br
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

from qgis.core import QgsFeatureRequest, QgsGeometry, QGis, QgsSpatialIndex, QgsCoordinateTransform

class ContourTool():
    def updateReference(self, referenceLayer):
        '''
        Updates the reference layer and updates the spatial index
        '''
        self.reference = referenceLayer
        self.populateIndex()

    def populateIndex(self):
        '''
        Populates the spatial index
        '''
        #spatial index
        self.index = QgsSpatialIndex()
        for feat in self.reference.getFeatures():
            self.index.insertFeature(feat)
            
    def getCandidates(self, bbox):
        '''
        Gets candidates using the spatial index to speedup the process
        '''
        #features that might satisfy the query
        ids = self.index.intersects(bbox)
        candidates = []
        for id in ids:
            candidates.append(self.reference.getFeatures(QgsFeatureRequest().setFilterFid(id)).next())
        return candidates            
            
    def getFeatures(self, geom):
        '''
        Gets the features that intersect geom to be updated
        '''
        #features that satisfy the query
        ret = []
        
        rect = geom.boundingBox()
        candidates = self.getCandidates(rect)
        for candidate in candidates:
            featGeom = candidate.geometry()
            if featGeom.intersects(geom):
                ret.append(candidate)
                
        return ret
    
    def getKey(self, item):
        '''
        Gets the key
        '''
        return item[0]
                
    def sortFeatures(self, geom, features):
        '''
        Sorts features according to the distance
        '''
        #sorting by distance
        distances = []
        
        firstPoint = geom.asPolyline()[0]
        pointGeom = QgsGeometry.fromPoint(firstPoint)

        for intersected in features:
            intersection = geom.intersection(intersected.geometry())
            if intersection.type() == QGis.Point:
                distance = intersection.distance(pointGeom)
                distances.append((distance, intersected))
        
        ordered = sorted(distances, key=self.getKey)
        #returning a list of tuples (distance, feature)
        return ordered

    def reproject(self, geom, canvasCrs):
        '''
        Reprojects geom to the reference layer crs
        '''
        destCrs = self.reference.crs()
        if canvasCrs.authid() != destCrs.authid():
            coordinateTransformer = QgsCoordinateTransform(canvasCrs, destCrs)
            geom.transform(coordinateTransformer)
    
    def assignValues(self, attribute, pace, geom, canvasCrs):
        '''
        Assigns attribute values to all features that intersect geom.
        '''
        self.reproject(geom, canvasCrs)
        features = self.getFeatures(geom)
        if len(features) == 0:
            return -2
        
        ordered = self.sortFeatures(geom, features)
        if len(ordered) == 0:
            return -1

        #the first feature must have the initial value already assigned
        first_feature = ordered[0][1]
        #getting the initial value
        first_value = first_feature.attribute(attribute)
        if not first_value:
            return -3

        #getting the filed index that must be updated
        fieldIndex = self.reference.fieldNameIndex(attribute)

        self.reference.startEditing()
        for i in range(1, len(ordered)):
            #value to be adjusted
            value = first_value + pace*i
            #feature that will be updated
            feature = ordered[i][1]
            #feature id that will be updated
            id = feature.id()
            #actual update in the layer
            if not self.reference.changeAttributeValue(id, fieldIndex, value):return 0
        return 1