import arcpy
#from arcpy import env
#from arcpy.ia import *
import os
import Dropboxing

def TIFCreator(InPath, OutPath, RegionUnit, StartYear, EndYear, replace, DropboxPath, DropboxUpload):
    EndYear1 = EndYear+1
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    print("Creating TIF for {}".format(RegionUnit))
    INPATH = InPath + "/" + str(RegionUnit) + "-Image"
    if not os.path.exists(INPATH):
        print("No original files found for {}".format(RegionUnit))
    else:
        OUTPATH = OutPath + "/" + str(RegionUnit)
        if not os.path.exists(OUTPATH):
            os.makedirs(OUTPATH)
        LISTDIR = []
        for filedir in os.listdir(INPATH):
            LISTDIR.append(os.path.join(INPATH, filedir))
        DICT = {}
        for year in range(StartYear, EndYear1):
            mergedname = str(RegionUnit) + "-" + str(year)
            if bool(replace) == True or not os.path.isfile(str(OUTPATH) + "/" + str(RegionUnit) + "-" + str(year) + ".tif"):
                DICT['y'+str(year)] = []
                for subdir in LISTDIR:
                    for file in os.listdir(subdir):
                        if file.endswith(str(year)+'.tif'):
                            raster = arcpy.Raster(os.path.join(subdir, file))
                            DICT['y'+str(year)].append(raster)
                if DICT['y'+str(year)]:
                    merged = arcpy.ia.Merge(DICT['y'+str(year)], "MIN")
                    merged.save(str(OUTPATH) + "/" + str(mergedname) + ".tif")
                    if bool(DropboxUpload) == True:
                        dbx = Dropboxing.DropboxConnector()
                        print("{}.tif ...".format(mergedname))
                        print("    ... created")
                        for file in ['.tif', '.tfw', '.tif.aux.xml', '.tif.vat.cpg', '.tif.vat.dbf']:
                            Local = str(OUTPATH) + "/" + str(mergedname) + str(file)
                            Dropbox = str(DropboxPath) + "/" + str(mergedname) + str(file)
                            Dropboxing.DropboxUploader(LocalFilePath=Local, DropboxFilePath=Dropbox)
                        print("    ... uploaded to Dropbox")
                    else:
                        print("{}.tif created".format(mergedname))
                else:
                    print("No original files found for {}".format(year))
            else:
                print("{}.tif already exists".format(mergedname))
    arcpy.env.overwriteOutput = False
    print(" ")

def GHSCreator(InPath, OutPath, Model, Year, replace):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    GHS_tif = []
    mergedname = 'GHS_'+str(Model)+'_E'+str(Year)+'_GLOBE_R2022A_54009_100_V1_0'
    if not os.path.exists(InPath):
        print("No original files found for GHS model {}".format(Model))
    else:
        print("Creating GHS tif for model "+str(Model+" in year "+str(Year)))
        if not os.path.exists(OutPath):
            os.makedirs(OutPath)
        if bool(replace) == True or not os.path.isfile(str(OutPath)+"/"+str(mergedname)+".tif"):
            for file in os.listdir(InPath):
                if file.startswith(mergedname) and file.endswith('.tif'):
                    raster = arcpy.Raster(os.path.join(InPath, file))
                    GHS_tif.append(raster)
            if GHS_tif:
                merged = arcpy.ia.Merge(GHS_tif, "MEAN")
                merged.save(str(OutPath)+"/"+str(mergedname)+".tif")
        else:
            print("{}.tif already exists".format(mergedname))
    arcpy.env.overwriteOutput = False
    print(" ")
