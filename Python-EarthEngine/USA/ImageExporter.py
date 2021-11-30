import logging
import ee
from ee.batch import Export
from ee import EEException
from ee.batch import Export

import CorineImages
import SatelliteImages
from USA.State import State
from Classify import Classify
from Training import Training
from USA.CrossValidationUSA import CrossValidationUSA
import DriveApi


class ImageExporter:
    def __init__(self):
        ee.Initialize()

    # def RunImage(self, states):
    #     #classifier = ExecuterUSA(states).GetTrainingsData()
    #     state = None
    #     for s in states:
    #         if s.GetName() == 'Texas':
    #             state = s
    #     #self.RunImage(state, classifier)

    def RunImage(self, state, classifier):
        print("State image export of: {}".format(state.GetName()))
        classify = Classify()
        rasterCells = state.GetGridCells()
        DriveApi.ManageImageFolders(state.GetName())
        imageProgress = DriveApi.CheckImageProgress(state.GetName(), rasterCells)

        if len(imageProgress[0]) == 0:
            state.stateDB.hasImages = True
            state.Save()
            print("no image left")
        else:
            # First cell not executed, execute
            cell = imageProgress[0][0]
            print("Total cells: {} , finished: {}: , todo: {}".format(len(rasterCells), len(rasterCells)-len(imageProgress[0]),len(imageProgress[0])))
            self.RunCellImage(state, classify, classifier, cell)

    def RunCellImage(self, state, classify, classifier, cell):
        DriveApi.CreateImageFolder(state.GetName(), cell)
        # cellname = rasterCells[0][0]
        # for r in rasterCells:
        #     if r[0] == cellname:
        #         rcell = r
        #  cell = rcell[0]
        smallGrid = ee.FeatureCollection(state.GetAssetName() + 'Grid/grid-' + str(cell))
        smallGrid = smallGrid.distinct('MGRS')

        start_year = 1982
        end_year = 2021

        imageCollection = classify.DoClassification(smallGrid, classifier, cell, 'MGRS', start_year, end_year,
                                             state.GetName(), False)
        #print(imageCollection.getInfo())
        #print(imageCollection.first().bandNames().getInfo())
        boundary = smallGrid.geometry()
        #years = ee.List.sequence(1982, 2019, 1)
        print('start cell export {}'.format(cell))

        #def exportGridCell(year):
        for year in range(start_year, end_year):
            image = imageCollection.filterMetadata('year', 'equals', year).first().select('classified')
            # Reduce region to border
            maskBorder = smallGrid.reduceToImage(properties=['Shape_Leng'], reducer=ee.Reducer.first())
            image = image.mask(maskBorder).unmask(9)

            filename = state.GetName() + '-image-' + str(cell) + "-" + str(year)
            foldername = state.GetName() + "-Image/" + str(cell)
            print(filename)
            Export.image.toDrive(
                image=image,
                folder=foldername,
                description=filename,
                scale=30,
                region=boundary).start()

        # year=2000
        # image = imageCollection.filterMetadata('year', 'equals', year).first().select('blue','red','green')
        # Export.image.toDrive(
        #     image=image,
        #     folder=foldername,
        #     description="image-"+str(year)+"-"+cell,
        #     scale=30,
        #     region=boundary).start()
        #years.map(exportGridCell)countryName + "-" + "image-" + str(cell[0]) + '-' + str(year) + ".tif"

        #image2000 = imageCollection.filterMetadata('year', 'equals', 2000).first().select('classified')
        #geom = ee.Geometry.Polygon([[-96.87509366579198,32.725772585947404], [-96.02914640016698,32.725772585947404], [-96.02914640016698,33.33253304176427], [-96.87509366579198,33.33253304176427], [-96.87509366579198,32.725772585947404]])
        #geom = ee.Geometry.Polygon([[-96.48679654528232,32.03915818156185],[-96.37804101635547,32.03915818156185], [-96.37804101635547,32.1114845887879], [-96.48679654528232,32.1114845887879], [-96.48679654528232,32.03915818156185]])
        # Export.image.toAsset(
        #     image=image2000,
        #     description='exportTexas3',
        #     assetId= 'users/emap1/test/' + 'exportTexas3',
        #     scale=30,
        #     region=smallGrid.geometry().bounds()).start()
        print("expo image")
        print("")

