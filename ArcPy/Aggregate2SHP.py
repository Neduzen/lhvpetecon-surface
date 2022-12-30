import arcpy
#from arcpy import env
from arcpy.ia import *
from arcpy.sa import *
import os
import pandas as pd
import numpy as np
import Dropboxing

def CSVCreator_SurfaceGroups(InPath, OutPath, Shapefile, ZoneField, replace, DropboxPath, DropboxUpload):
    arcpy.CheckOutExtension("Spatial")
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    OutName = OutPath[::-1][:OutPath[::-1].find("/")][::-1]
    print("Creating surface groups CSV for {}".format(OutName))
    if not os.path.exists(InPath):
        print("No merged TIF files found in {}".format(InPath))
    else:
        for file in os.listdir(InPath):
            if file.startswith('Reclass'):
                os.remove(InPath+"/"+file)  # necessary if CSVMerger_SurfaceGroup started before and stopped temporarily
        if not os.path.exists(OutPath):
            os.makedirs(OutPath)
        InValueRasters = []
        for tif in os.listdir(InPath):
            if tif.endswith('.tif'):
                InValueRasters.append(os.path.join(InPath, tif))
        SurfaceMap = {'builtup': [0], 'grass': [1], 'crops': [2], 'forest': [3], 'noveg': [4], 'water': [5], 'cloud': [9]}
        for sg in SurfaceMap:
            for raster in InValueRasters:
                year = raster[::-1][4:8][::-1]
                OutCSV = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1]+"_"+year+"_"+sg+".csv"
                if bool(replace) == True or not os.path.isfile(str(OutPath) + "/" + str(OutCSV)):
                    ReclassRaster = Reclassify(raster, "Value", RemapValue([[SurfaceMap[sg][0],1]]), "NODATA")
                    OutTable = OutPath+"/"+OutCSV[::-1][4:][::-1]+".dbf"
                    ZonalStatisticsAsTable(Shapefile, ZoneField, ReclassRaster, OutTable, "DATA", "SUM")
                    arcpy.TableToTable_conversion(OutTable, OutPath, OutCSV)
                    os.remove(OutTable)
                    if bool(DropboxUpload) == True:
                        dbx = Dropboxing.DropboxConnector()
                        OutCPG = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1]+"_"+year+"_"+sg+".cpg"
                        OutCSVXML = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1]+"_"+year+"_"+sg+".csv.xml"
                        OutDBFXML = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1]+"_"+year+"_"+sg+".dbf.xml"
                        print("{} ...".format(OutCSV))
                        print("    ... created")
                        for file in [str(OutCSV), str(OutCPG), str(OutCSVXML), str(OutDBFXML)]:
                            Local = str(OutPath) + "/" + file
                            Dropbox = str(DropboxPath) + "/" + file
                            Dropboxing.DropboxUploader(LocalFilePath=Local, DropboxFilePath=Dropbox)
                        print("    ... uploaded to Dropbox")
                    else:
                        print("{} created".format(OutCSV))
                else:
                    print("{} already exists".format(OutCSV))
    arcpy.CheckInExtension("Spatial")


def CSVMerger_SurfaceGroups(InPath, OutPath, replace, DropboxPath, DropboxUpload):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    OutName = OutPath[::-1][:OutPath[::-1].find("/")][::-1]
    print("Merging surface groups CSVs for {}".format(OutName))
    if not os.path.exists(InPath):
        print("No CSV files found in {}".format(InPath))
    else:
        if not os.path.exists(OutPath):
            os.makedirs(OutPath)
        CSVDict = {}
        for csv in os.listdir(InPath):
            if csv.endswith('builtup.csv') or csv.endswith('grass.csv') or csv.endswith('forest.csv') or csv.endswith('crops.csv') or csv.endswith('noveg.csv') or csv.endswith('water.csv') or csv.endswith('cloud.csv'):
                sg = csv[::-1][4:csv[::-1].find("_")][::-1]
                year = csv[::-1][csv[::-1].find("_")+1:][:4][::-1]
                pathcsv = InPath+"/"+csv
                CSVDict[pathcsv] = [sg, year, "no"]
        if bool(CSVDict) == False:
            print("No CSV files found in {}".format(InPath))
        else:
            for csv1 in CSVDict:
                if CSVDict[csv1][2] == "no":
                    df1 = pd.read_csv(csv1, delimiter=";")
                    df1 = df1.rename(columns={"SUM": CSVDict[csv1][0]+"_px", "AREA": CSVDict[csv1][0]+"_area"})
                    df1 = df1.drop(columns=["OID_", "COUNT"])
                    if "ZONE_CODE" in df1:
                        df1 = df1.drop(columns=["ZONE_CODE"])
                    CSVDict[csv1][2] = "yes"
                    for csv2 in CSVDict:
                        if CSVDict[csv2][2] == "no" and CSVDict[csv2][1] == CSVDict[csv1][1]:
                            df2 = pd.read_csv(csv2, delimiter=";")
                            df2 = df2.rename(columns={"SUM": CSVDict[csv2][0]+"_px", "AREA": CSVDict[csv2][0]+"_area"})
                            df2 = df2.drop(columns=["OID_", "COUNT"])
                            if "ZONE_CODE" in df2:
                                df2 = df2.drop(columns=["ZONE_CODE"])
                            if not df2.empty:
                                df1 = df1.merge(df2, how='outer', on=df1.columns[0], sort=True, validate='one_to_one')
                            else:
                                df1[CSVDict[csv2][0]+"_px"] = np.nan
                            CSVDict[csv2][2] = "yes"
                    df1.insert(1, 'year', CSVDict[csv1][1])
                    df1 = df1.fillna(0)
                    df1name = csv1[::-1][:csv1[::-1].find("/")][::-1][:csv1[::-1][:csv1[::-1].find("/")][::-1].rfind(CSVDict[csv1][1])]+CSVDict[csv1][1]+".csv"
                    OutFile_comma = OutPath+"/"+"_comma_"+df1name
                    OutFile = OutPath+"/"+df1name
                    if bool(replace) == True or not os.path.isfile(str(OutFile)):
                        df1.to_csv(OutFile_comma, sep=";", index=False, encoding='utf-8')
                        comma = open(OutFile_comma, "rt")
                        dot = open(OutFile, "wt")
                        for line in comma:
                            dot.write(line.replace(',', '.'))
                        comma.close()
                        dot.close()
                        os.remove(OutFile_comma)
                        if bool(DropboxUpload) == True:
                            dbx = Dropboxing.DropboxConnector()
                            print("{} ...".format(df1name))
                            print("    ... created")
                            Dropbox = str(DropboxPath) + "/" + str(df1name)
                            Dropboxing.DropboxUploader(LocalFilePath=OutFile, DropboxFilePath=Dropbox)
                            print("    ... uploaded to Dropbox")

                        else:
                            print("{} created".format(df1name))
                    else:
                        print("{} already exists".format(df1name))


def CSVCreator_NightLightIntensity(InPath, OutPath, Shapefile, ZoneField, nl_type, replace):
    arcpy.CheckOutExtension("Spatial")
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    OutName = OutPath[::-1][:OutPath[::-1].find("/")][::-1]
    if nl_type == 'DMSP' or nl_type == 'VIIRS':
        print("Creating "+str(nl_type)+" night light intensity CSV for {}".format(OutName))
        if not os.path.exists(InPath):
            print("No "+str(nl_type)+" source files found in {}".format(InPath))
        else:
            if not os.path.exists(OutPath):
                os.makedirs(OutPath)
            InValueRasters = []
            for file in os.listdir(InPath):
                if nl_type == 'DMSP':
                    if file.endswith('stable_lights.avg_vis.tif'):
                        InValueRasters.append(InPath+"/"+file)
                elif nl_type == 'VIIRS':
                    if file.endswith('average_masked.tif'):
                        InValueRasters.append(InPath+"/"+file)
            for raster in InValueRasters:
                filename = raster[::-1][:raster[::-1].find("/")][::-1]
                if nl_type == 'DMSP':
                    namespec = filename[:7]
                    OutCSV = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1] + "_" + str(namespec) + "_DMSPOLSv4c.csv"
                elif nl_type == 'VIIRS':
                    if filename[23:31].find("_") == -1:
                        namespec = filename[23:31]+filename[11:15]
                    else:
                        namespec = filename[23:29]+filename[11:15]
                    OutCSV = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1] + "_" + str(namespec) + "_VIIRSv2.csv"
                if bool(replace) == True or not os.path.isfile(str(OutPath) + "/" + str(OutCSV)):
                    OutTable = OutPath+"/"+OutCSV[::-1][4:][::-1]+".dbf"
                    ZonalStatisticsAsTable(Shapefile, ZoneField, raster, OutTable, "DATA", "MEAN")
                    arcpy.TableToTable_conversion(OutTable, OutPath, OutCSV)
                    os.remove(OutTable)
                    print("{} created".format(OutCSV))
                else:
                    print("{} already exists".format(OutCSV))
    else:
        print("nl_type has to be either DMSP or VIIRS. No night light intensity CSV created. Carrying on with next tasks.")
        pass
    arcpy.CheckInExtension("Spatial")

def CSVCreator_GHSL(InPath, OutPath, Shapefile, ZoneField, ghs_type, replace):
    arcpy.CheckOutExtension("Spatial")
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    OutName = OutPath[::-1][:OutPath[::-1].find("/")][::-1]
    if ghs_type == 'BUILT_S' or ghs_type == 'BUILT_V':
        print("Creating "+str(ghs_type)+" GHS CSV for {}".format(OutName))
        if not os.path.exists(InPath):
            print("No "+str(ghs_type)+" GHS source files found in {}".format(InPath))
        else:
            if not os.path.exists(OutPath):
                os.makedirs(OutPath)
            InValueRasters = []
            for file in os.listdir(InPath):
                if file.startswith('GHS_'+str(ghs_type)) and file.endswith('.tif'):
                    InValueRasters.append(InPath+"/"+file)
            for raster in InValueRasters:
                filename = raster[::-1][:raster[::-1].find("/")][::-1]
                namespec = filename[:17]
                OutCSV = Shapefile[::-1][4:Shapefile[::-1].find("/")][::-1] + "_" + str(namespec) + ".csv"
                if bool(replace) == True or not os.path.isfile(str(OutPath) + "/" + str(OutCSV)):
                    OutTable = OutPath+"/"+OutCSV[::-1][4:][::-1]+".dbf"
                    ZonalStatisticsAsTable(Shapefile, ZoneField, raster, OutTable, "DATA", "SUM")
                    arcpy.TableToTable_conversion(OutTable, OutPath, OutCSV)
                    os.remove(OutTable)
                    print("{} created".format(OutCSV))
                else:
                    print("{} already exists".format(OutCSV))
    else:
        print("ghs_type has to be either BUILT_S or BUILT_V. No CSV created. Carrying on with next tasks.")
        pass
    arcpy.CheckInExtension("Spatial")
