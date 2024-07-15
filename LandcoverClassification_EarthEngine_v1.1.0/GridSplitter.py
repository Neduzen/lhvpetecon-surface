import ee
from ee.batch import Export


class GridSplitter:
    # Takes the Feature Country border, calculates the area and splits it into smaller cells.
    def SplitGrid(self, feature, assetName, manualGridCells=[]):
        gridCells = []

        # If no manual grid cells given, create bounding box and its grid cells from the feature
        if len(manualGridCells) == 0:
            n1, e1, n2, e2 = self.getBoundingCoordinates(feature)
            for c in self.getCordinateList(n1, n2, e1, e2):
                gridCells.append((c, False))
        else:
            gridCells = manualGridCells

        polygonList = ee.List([])
        gridCellFeatures = ee.FeatureCollection(ee.List([]))
        for g in gridCells:
            #cellfeat = self.createPolygon(g[0])
            newfeat = ee.FeatureCollection(self.createPolygon(g[0])).filterBounds(feature)
            if len(newfeat.getInfo()['features'])>0:
                gridCellFeatures = gridCellFeatures.merge(newfeat)

            #polygonList = polygonList.add(cellfeat)

        #gridCellFeatures = ee.FeatureCollection(polygonList)

        gridCellFeatures = gridCellFeatures.filterBounds(feature) # Exclude cells not in feature area
        gridCellFeatures = gridCellFeatures.distinct('CellID')  # Only one CellID, no duplicates

        gridInfo = gridCellFeatures.getInfo()
        # Add 1 degree lat long grid cells to country
        gridCells = []
        for gtext in gridInfo['features']:
            fullCellId = gtext['properties']['CellID']
            if (fullCellId, False) not in gridCells and (fullCellId, True) not in gridCells:
                gridCells.append((fullCellId, False))

        # Export grid cells
        task = Export.table.toAsset(
            collection=gridCellFeatures,
            description="grid",
            assetId=assetName
        )
        task.start()

        print("1'degree cells for country: {}".format(gridCells))
        return gridCells

    # Calculates from given coordinates all potential grid cells within the the coordinates.
    # 1 degree lat and long grid cell sizes
    def getCordinateList(self, long1, long2, lat1, lat2):
        # Get max and min lat and long (in real numbers)
        if lat1 <= lat2:
            n1 = int(lat1)

            n2 = int(lat2)
        else:
            n1 = int(lat2)
            n2 = int(lat1)
        if n1 < 0:
            n1 -= 1
        if n2 > 0:
            n2 += 1
            # ee.Number(ee.Algorithms.If(e1t.gte(e2t), e2t, e1t)).int()
        if long1 <= long2:
            e1 = int(long1)
            e2 = int(long2)
        else:
            e1 = int(long2)
            e2 = int(long1)
        if e1 < 0:
            e1 -= 1
        if n2 > 0:
            e2 += 1

        cellList = []
        i = n1
        while i < n2:
            j = e1
            while j < e2:
                cellList.append("Long:" + str(j) + ",Lat:" + str(i))
                j += 1
            i += 1

        return cellList

    # Generates a bounding box for a given feature and returns coordinates.
    def getBoundingCoordinates(self, feature):
        coords = ee.List(feature.geometry().bounds().coordinates().get(0))
        n1t = ee.Number(ee.List(coords.get(0)).get(0))
        e1t = ee.Number(ee.List(coords.get(0)).get(1))
        n2t = ee.Number(ee.List(coords.get(2)).get(0))
        e2t = ee.Number(ee.List(coords.get(2)).get(1))
        # Get max and min lat and long (in real numbers)
        e1 = ee.Number(ee.Algorithms.If(e1t.gte(e2t), e2t, e1t)).int().getInfo()
        e2 = ee.Number(ee.Algorithms.If(e1t.gte(e2t), e1t, e2t))
        n1 = ee.Number(ee.Algorithms.If(n1t.gte(n2t), n2t, n1t)).int().getInfo()
        n2 = ee.Number(ee.Algorithms.If(n1t.gte(n2t), n1t, n2t))
        n2 = ee.Number(n2).int().add(1).getInfo()
        e2 = ee.Number(e2).int().add(1).getInfo()
        return (n1, e1, n2, e2)

    # Create a polygon based on the cell name which includes the lat and long coordinates
    def createPolygon(self, cell):
        long = ee.Number(int(cell.split(",")[0].split(":")[1]))
        lat = ee.Number(int(cell.split(",")[1].split(":")[1]))
        lat1 = lat.add(1)
        long1 = long.add(1)
        coords = ee.List([[long1, lat], [long, lat], [long, lat1], [long1, lat1], [long1, lat]])
        poly = ee.Geometry.Polygon(coords)
        feat = ee.Feature(poly).set("Long", long).set("Lat", lat).set("CellID", cell)
        return feat