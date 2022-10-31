from qgis import processing
from qgis.core import *
import qgis.utils
from qgis.core import QgsVectorLayer
from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsPointXY,
    QgsRaster,
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
    QgsSingleBandColorDataRenderer,
    QgsSingleBandGrayRenderer,
    QgsFeatureRequest
)

from qgis.PyQt.QtGui import (
    QColor,
)

from osgeo import gdal

# download the raw population raster layer here: https://ghsl.jrc.ec.europa.eu/ghs_pop2022.php
rlayer = QgsProject.instance().mapLayersByName('GHS_POP_E2020_GLOBE_R2022A_54009_100_V1_0')
# get the resolution of the raster in layer unit
#print(rlayer.width(), rlayer.height())

# create this mask using the urban centers database here: http://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_STAT_UCDB2015MT_GLOBE_R2019A/V1-2/
shapefile = 'G:/CodingProjects/leoTemp/data/processed/UA_mask_small.shp'

layer = QgsVectorLayer(shapefile, 'UA_mask_small.shp', 'ogr')

if not layer.isValid():
    raise Exception('Layer is not valid')
    
#it = layer.getFeatures((QgsFeatureRequest().setFilterFid(12914)))
it = layer.getFeatures()

i = 0

for feature in it:
    featureID = int(feature["ID_HDC_G0"])
    featureName = feature["UC_NM_MN"]
    mask = "G:/CodingProjects/leoTemp/data/interim/{}.shp".format(str(int(featureID)))
    outputRas = "G:/CodingProjects/leoTemp/data/processed/UArasters/{}.tif".format(str(int(featureID)))
    outputPoly = "G:/CodingProjects/leoTemp/data/processed/UApolys/{}.shp".format(str(int(featureID)))

    print("Clipping feature {}".format(featureID))
    print("{}".format(featureName))
    #selFeature = layer.selectByExpression("\"ID_HDC_G0\"'{}' ".format(featureID))
    #layer.setSubsetString("ID_HDC_G0 = {}".format(featureID))
    #layer.selectByExpression("ID_HDC_G0 = {}".format(featureID))
    #selFeature[0]
    processing.run("gdal:cliprasterbymasklayer", {
        'INPUT':'G:/CodingProjects/leoTemp/data/GHS_POP_E2020_GLOBE_R2022A_54009_100_V1_0.tif',
        'MASK':QgsProcessingFeatureSourceDefinition(
            mask, 
            selectedFeaturesOnly=False, 
            featureLimit=-1, 
            geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
        'SOURCE_CRS':None,
        'TARGET_CRS':None,
        'NODATA':None,
        'ALPHA_BAND':False,
        'CROP_TO_CUTLINE':True,
        'KEEP_RESOLUTION':False,
        'SET_RESOLUTION':False,
        'X_RESOLUTION':None,
        'Y_RESOLUTION':None,
        'MULTITHREADING':False,
        'OPTIONS':'',
        'DATA_TYPE':0,
        'EXTRA':'',
        'OUTPUT':outputRas})
    
    print("converting to polygons")
    processing.run("native:pixelstopolygons", {
    'INPUT_RASTER':outputRas,
    'RASTER_BAND':1,
    'FIELD_NAME':'VALUE',
    'OUTPUT':outputPoly})
    #layer.setSubsetString("")
    #layer.selectByExpression("")
    i=i+1
    print("processed " + str(i) +"/3261 urban areas")

print("done")
    
    
    
    
    
    
