import ee
from ee.batch import Export
from Classify import Classify
import DriveApi


class ImageExporter:
    def __init__(self):
        ee.Initialize()

    def RunImage(self, state, classifier, start_year, end_year):
        print("State image export of: {}".format(state.GetName()))
        self.start_year = start_year
        self.end_year = end_year
        self.state = state
        self.classifier = classifier

        # Shift folders with exported images to correct place and check classification progress
        rasterCells = state.GetGridCells()
        DriveApi.ManageImageFolders(state.GetName())
        imageProgress = DriveApi.CheckImageProgress(state.GetName(), rasterCells, self.start_year, self.end_year)

        # If not finished, export next cell, else mark as finished
        if len(imageProgress[0]) == 0:
            state.stateDB.hasImages = True
            state.Save()
            print("no image left")
            return 0
        else:
            # First cell not executed, execute
            cell = imageProgress[0][0]
            print("Total cells: {} , finished: {}: , todo: {}".format(len(rasterCells), len(rasterCells)-len(imageProgress[0]),len(imageProgress[0])))
            self.RunCellImage(cell)
            return 1

    def RunCellImage(self, cell):
        DriveApi.CreateImageFolder(self.state.GetName(), cell)
        classify = Classify()

        # From -23.99 degree to +23.99 degree all year, else exclude winter (South or North)
        latitude = int(cell.split(",")[1].split(":")[1])
        latitudeRegion = "Equator"
        if latitude >= 24:
            latitudeRegion = "North"
        elif latitude < -24:
            latitudeRegion = "South"

        # Get grid cell and export it
        smallGrid = ee.FeatureCollection(self.state.GetAssetName() + 'GridState')
        smallGrid = smallGrid.distinct('CellID')
        smallGrid = smallGrid.filter(ee.Filter.eq("CellID", cell))
        imageCollection = classify.DoClassification(smallGrid, self.classifier, cell, 'CellID', self.start_year,
                                                    self.end_year, self.state.GetName(), False, latitudeRegion)
        boundary = smallGrid.geometry()
        print('start cell export {}'.format(cell))

        # Take classified image for each year and export it
        for year in range(self.start_year, self.end_year):
            # Get classified image
            image = imageCollection.filterMetadata('year', 'equals', year).first().select('classified')

            # Reduce region to border
            def setNr(feat):
                return feat.set("ID", 1)
            maskBorder = self.state.GetFeature().map(setNr).reduceToImage(properties=['ID'], reducer=ee.Reducer.first())
            image = image.mask(maskBorder).unmask(9)

            filename = self.state.GetName() + '-image-' + str(cell) + "-" + str(year)
            foldername = self.state.GetName() + "-Image/" + str(cell)
            print(filename)
            Export.image.toDrive(
                image=image,
                folder=foldername,
                description=filename,
                scale=30,
                region=boundary).start()

        print("export images")
        print("")

