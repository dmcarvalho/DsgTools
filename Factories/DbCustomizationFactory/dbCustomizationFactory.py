# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2016-07-31
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba@dsg.eb.mil.br
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
#DsgTools imports
from DsgTools.Factories.DbCustomizationFactory.classCustomization import ClassCustomization
from DsgTools.Factories.DbCustomizationFactory.codeNameCustomization import CodeNameCustomization
from DsgTools.Factories.DbCustomizationFactory.attributeCustomization import AttributeCustomization
from DsgTools.Factories.DbCustomizationFactory.domainCustomization import DomainCustomization
from DsgTools.Factories.DbCustomizationFactory.nullityCustomization import NullityCustomization
from DsgTools.Factories.DbCustomizationFactory.defaultCustomization import DefaultCustomization

class DbCustomizationFactory:
    def createCustomization(self, type, validatedJSONDict):
        if type == 'class':
            return ClassCustomization(validatedJSONDict)
        if type == 'codeName':
            return CodeNameCustomization(validatedJSONDict)
        if type == 'attribute':
            return AttributeCustomization(validatedJSONDict)
        if type == 'domain':
            return DomainCustomization(validatedJSONDict)
        if tyle == 'nullity':
            return NullityCustomization(validatedJSONDict)
        if tyle == 'default':
            return DefaultCustomization(validatedJSONDict)