import arcpy
import os

def CoordinatesToSquareBuffer(InCoordTable, InCoordX, InCoordY, OutSHP, BufferDist, replace):
    if bool(replace) == True:
        arcpy.env.overwriteOutput = True
    if not os.path.isfile(OutSHP) or bool(replace) == True:
        print("Creating Square Buffer SHP from {}".format(InCoordTable))
        TempCoordClass = "memory/TempCoordClass"
        TempCircleSHP = "memory/TempCircleSHP"
        arcpy.XYTableToPoint_management(InCoordTable, TempCoordClass, InCoordX, InCoordY)
        arcpy.Buffer_analysis(TempCoordClass, TempCircleSHP, BufferDist)
        arcpy.MinimumBoundingGeometry_management(TempCircleSHP, OutSHP, "ENVELOPE", "NONE")
        print("{} created".format(OutSHP))
        #OutDBF = OutSHP[::-1][4:][::-1] + ".dbf"
        #OutPath = OutSHP[::-1][OutSHP[::-1].find("/"):][::-1]
        #OutCSV = OutSHP[::-1][4:OutSHP[::-1].find("/")][::-1] + ".csv"
        #arcpy.TableToTable_conversion(OutDBF, OutPath, OutCSV)
        #print("{} created".format(OutCSV))
        arcpy.env.overwriteOutput = False
        arcpy.Delete_management(TempCoordClass)
        arcpy.Delete_management(TempCircleSHP)
    else:
        print("{} already exists".format(OutSHP))
    print(" ")
