import arcpy
import os
import pandas as pd
import math

def ShapeSplitter(SHP, TargetSize, OutPath, replace):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    if not os.path.exists(OutPath):
        os.makedirs(OutPath)
    SHPName = SHP[::-1][:SHP[::-1].find("/")][::-1][:SHP[::-1][:SHP[::-1].find("/")][::-1].find(".shp")]
    SHPCopy = OutPath+"/"+SHPName+"_copy.shp"
    print("Splitting {} ...".format(SHP))
    if not os.path.isfile(SHPCopy) or bool(replace) == True:
        arcpy.CopyFeatures_management(SHP, SHPCopy)
        arcpy.AddField_management(SHPCopy, "OBJ_GROUP", "LONG")
        splitExpression = "math.floor(!FID!/"+str(TargetSize)+")"
        arcpy.CalculateField_management(SHPCopy, "OBJ_GROUP", splitExpression)
        SplitPath = OutPath+"/"+SHPName+"_splits"
        if not os.path.exists(SplitPath):
            os.makedirs(SplitPath)
        elif bool(replace) == True:
            for file in os.listdir(SplitPath):
                os.remove(os.path.join(SplitPath, file))
        arcpy.SplitByAttributes_analysis(SHPCopy, SplitPath, "OBJ_GROUP")
        for file in os.listdir(SplitPath):
            prefixfile = SHPName+"_"+file
            os.rename(os.path.join(SplitPath, file), os.path.join(SplitPath, prefixfile))
        print("... successfully splitted into {} blocks".format(TargetSize))
    else:
        print("... splits of {} already exist".format(SHP))

def SmallShapeInLargeShape(SmallSHP, SmallZoneField, LargeSHP, LargeZoneField, OutPath, replace):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    SmallSHPName = SmallSHP[::-1][:SmallSHP[::-1].find("/")][::-1][:SmallSHP[::-1][:SmallSHP[::-1].find("/")][::-1].find(".shp")]
    LargeSHPName = LargeSHP[::-1][:LargeSHP[::-1].find("/")][::-1][:LargeSHP[::-1][:LargeSHP[::-1].find("/")][::-1].find(".shp")]
    OutCSVName = SmallSHPName+"_in_"+LargeSHPName+".csv"
    OutCSV = OutPath+"/"+OutCSVName
    print("Creating {} ...".format(OutCSVName))
    if not os.path.isfile(OutCSV) or bool(replace) == True:
        #TempCentroidSHP = "memory/TempCentroidSHP"
        #TempJoinSHP = "memory/TempJoinSHP"
        TempCentroidSHP = OutPath+"/TempCentroidSHP.shp"
        TempJoinSHP = OutPath+"/TempJoinSHP.shp"
        #arcpy.CopyFeatures_management(SmallSHP, TempCentroidSHP)
        #arcpy.CalculateGeometryAttributes_management(TempCentroidSHP, [["lon", "CENTROID_X"], ["lat", "CENTROID_Y"]], "DD")
        arcpy.FeatureToPoint_management(SmallSHP, TempCentroidSHP, "CENTROID")
        arcpy.SpatialJoin_analysis(LargeSHP, TempCentroidSHP, TempJoinSHP, "JOIN_ONE_TO_MANY", "KEEP_COMMON")
        arcpy.TableToTable_conversion(TempJoinSHP, OutPath, OutCSVName)
        csv = pd.read_csv(OutCSV, sep=';', header=0)
        if len(csv) == 0:
            print("... {} is empty".format(OutCSV))
            os.remove(OutCSV)
            os.remove(OutCSV+'.xml')
        else:
            csv = csv[[SmallZoneField, LargeZoneField]]
            csv.to_csv(OutCSV, index=False)
            for file in os.listdir(OutPath):
                if file.startswith('TempCentroidSHP') or file.startswith('TempJoinSHP'):
                    os.remove(OutPath+"/"+file)
            print("... {} created".format(OutCSV))
    else:
        print("... {} already exists".format(OutCSV))
    print(" ")

def CSVAppender(InPath, OutPath, NameBegin, NameEnd, DeleteOrig=False, replace=False):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    OutName = NameBegin+"_in_"+NameEnd+".csv"
    OutCSV = OutPath+"/"+OutName
    if not os.path.isfile(OutCSV) or bool(replace) == True:
        print("Creating {} ...".format(OutName))
        ListFiles = []
        ListXMLs = []
        for file in os.listdir(InPath):
            if file.startswith(NameBegin) and file.endswith(NameEnd+'.csv'):
                ListFiles.append(InPath+"/"+file)
            if file.startswith(NameBegin) and file.endswith(NameEnd + '.csv.xml'):
                ListXMLs.append(InPath+"/"+file)
        csv = pd.concat([pd.read_csv(file) for file in ListFiles])
        csv.to_csv(OutCSV, index=False)
        if DeleteOrig == True:
            for file in ListFiles:
                os.remove(file)
            for file in ListXMLs:
                os.remove(file)
    else:
        print("{} already exists.".format(OutCSV))