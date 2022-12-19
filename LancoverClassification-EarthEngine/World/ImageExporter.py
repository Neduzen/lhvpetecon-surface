import ee
from ee.batch import Export
from Classify import Classify
import DriveApi


# Classifies the image and export it to the google drive.
class ImageExporter:
    def __init__(self):
        ee.Initialize()

    # Launches the execution of
    def RunImage(self, country, classifier, start_year, end_year):
        print("State image export of: {}".format(country.GetName()))
        self.start_year = start_year
        self.end_year = end_year
        self.country = country
        self.classifier = classifier

        # Shift folders with exported images to correct place and check classification progress
        rasterCells = country.GetGridCells()
        DriveApi.ManageImageFolders(country.GetName())
        imageProgress = DriveApi.CheckImageProgress(country.GetName(), rasterCells, self.start_year, self.end_year)

        # If not finished, export next cell, else mark as finished
        if len(imageProgress[0]) == 0:
            country.CountryWDB.hasImages = True
            country.Save()
            print("no image left")
        else:
            # Execute the first cell which is not yet finished
            cell = imageProgress[0][0]
            print("Total cells: {} , finished: {}: , todo: {}".format(len(rasterCells), len(rasterCells)-len(imageProgress[0]),len(imageProgress[0])))
            self.RunCellImage(cell)

    # Executes the grids cells classification.
    def RunCellImage(self, cell):
        # Create folder in the google drive.
        DriveApi.CreateImageFolder(self.country.GetName(), cell)
        classify = Classify()

        # From -23.99 degree to +23.99 degree images of the whole year are taken.
        # Else winter images are excluded (South or North).
        latitude = int(cell.split(",")[1].split(":")[1])
        latitudeRegion = "Equator"
        if latitude >= 24:
            latitudeRegion = "North"
        elif latitude < -24:
            latitudeRegion = "South"

        # Get grid cell and export it
        smallGrid = ee.FeatureCollection(self.country.GetAssetName() + 'Grid')
        smallGrid = smallGrid.distinct('CellID')
        smallGrid = smallGrid.filter(ee.Filter.eq("CellID", cell))
        imageCollection = classify.DoClassification(smallGrid, self.classifier, cell, 'CellID', self.start_year,
                                                    self.end_year, self.country.GetName(), False, latitudeRegion)
        boundary = smallGrid.geometry()
        print('start cell export {}'.format(cell))

        # Take classified image for each year and export it
        for year in range(self.start_year, self.end_year):
            # Get classified image
            image = imageCollection.filterMetadata('year', 'equals', year).first().select('classified')

            # Reduce region to border
            def setNr(feat):
                return feat.set("ID", 1)
            maskBorder = self.country.GetFeature().map(setNr).reduceToImage(properties=['ID'], reducer=ee.Reducer.first())
            image = image.mask(maskBorder).unmask(9)

            # Export image to google drive
            filename = self.country.GetName() + '-image-' + str(cell) + "-" + str(year)
            foldername = self.country.GetName() + "-Image/" + str(cell)
            print(filename)
            Export.image.toDrive(
                image=image,
                folder=foldername,
                description=filename,
                scale=30,
                region=boundary).start()

        print("export images")
        print("")

