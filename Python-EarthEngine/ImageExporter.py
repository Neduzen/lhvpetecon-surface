import logging
import ee
from ee.batch import Export
from Classify import Classify
import DriveApi


class ImageExporter:
    def __init__(self):
        ee.Initialize()

    def ExportCellImage(self, country, classifier, cellName, cellArea, start_year, end_year):
        classify = Classify()
        DriveApi.CreateImageFolder(country.GetName(), cellName)

        # Run Classification
        imageCollection = classify.DoClassification(cellArea, classifier, cellName, 'MGRS', start_year, end_year,
                                                    country.GetName(), False)
        print('start cell export {}'.format(cellName))

        for year in range(start_year, end_year):
            # Filter Image
            image = imageCollection.filterMetadata('year', 'equals', year).first().select('classified')
            # Reduce region to border
            maskBorder = cellArea.reduceToImage(properties=['EofOrigin'], reducer=ee.Reducer.first())
            image = image.mask(maskBorder).unmask(9)

            # Export image
            filename = country.GetName() + '-image-' + str(cellName) + "-" + str(year)
            foldername = country.GetName() + "-Image/" + str(cellName)
            print(filename)
            Export.image.toDrive(
                image=image,
                folder=foldername,
                description=filename,
                scale=30,
                region=cellArea.geometry()).start()
        print("")

