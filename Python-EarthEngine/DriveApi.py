from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
#SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata.readonly']

def Initialize():
    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def GetCountryFolderID(service, countryName, topicName):
    results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder'",
                                   pageSize=200, fields="nextPageToken, files(id, name)").execute()
    countryId = None
    for file in results.get('files', []):
        # Process change
        if file.get('name') == countryName + topicName:
            # Right country
            countryId = file.get('id')
            break
    return countryId

def GetImageSubFolderIDs(service, countryName, topicName):
    results = service.files().list(q="'0ALY842rGX6XaUk9PVA' in parents and mimeType = 'application/vnd.google-apps.folder'",
                                   pageSize=300, fields="nextPageToken, files(id, name, parents)").execute()
    countryIds = []
    for file in results.get('files', []):
        # Process change
        if countryName + topicName in str(file.get('name')):
            # Right country
            countryIds.append(file)
    return countryIds

def CheckClassificationProgress(countryName, gridCells):
    folderpart = "-Classification"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)

    # No grid cells splitted
    if len(gridCells) == 0:
        return gridCells, False

    # All possible files names
    allClassifyFiles = []
    classifyFolderNames = ['cloudfree', 'builtup', 'gras', 'crops', 'forest', 'noveg', 'water', 'totalPixel']
    for cell in gridCells:
        if not cell[1]:
            for name in classifyFolderNames:
                allClassifyFiles.append(name + "-" + str(cell[0]) + ".csv")

    # If all files already executed, return True
    if len(allClassifyFiles) == 0:
        return gridCells, True

    countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is not None:
        results = service.files().list(q="'{}' in parents".format(countryId), pageSize=1000, fields="nextPageToken, files(id, name)").execute()

        for file in results.get('files', []):
            # Process change
            if file.get('name') in allClassifyFiles:
                # Right country
                allClassifyFiles.remove(file.get('name'))
                    # if gridCells[gridCells.index((gridNumber, False))] is not None:
                    #     gridCellsCount[gridCells.index((gridNumber, False))] = (gridNumber, gridCellsCount[gridCells.index((gridNumber, False))][1]+1)
                    #     #gridCells[gridCells.index((gridNumber, False))] = (gridNumber, True)
                    #TODO DO smthng

        if len(allClassifyFiles) == 0:
            # Update gridCells to finished, if all files exist
            for i in range(0, len(gridCells)):
                gridCells[i] = (gridCells[i][0], True)
            # All done
            return gridCells, True
        else:
            for i in range(0, len(gridCells)):
                if not any('-' + str(gridCells[i][0]) + ".csv" in s for s in allClassifyFiles):
                    # All classes exported for cell, then set to true
                    gridCells[i] = (gridCells[i][0], True)
            # Return False, if not all files are in the GoogleDrive
            return gridCells, False
    else:
        logging.warning("No country folder in google drive found for country: {}".format(countryName))
        return gridCells, False
        #raise Exception("No country folder in google drive found for country: {}".format(countryName))

def CheckCrossValidationData(countryName, hasAllCorine):
    folderpart = "-CrossValidation"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)
    countryId = GetCountryFolderID(service, countryName, folderpart)

    # Define all needed files
    name = 'crossVal'
    years = [2000, 2006, 2012, 2018]
    if hasAllCorine:
        years.append(1990)
    allNeededFiles = []
    for i in range(1, 6):
        for y in years:
            filename = name + str(y) + "-subset" + str(i) + ".csv"
            allNeededFiles.append(filename)

    # Get all files within the country's Cross Validation folder.
    if countryId is not None:
        results = service.files().list(q="'{}' in parents".format(countryId),
                                       pageSize=100, fields="nextPageToken, files(id, name)").execute()
        for file in results.get('files', []):
            # Process change
            if file.get('name') in allNeededFiles:
                # CrossValidation File exist, remove from list
                allNeededFiles.remove(file.get('name'))

        if len(allNeededFiles) == 0:
            # All done
            return True
        else:
            return False

def CheckUSACrossValidationData(stateName):
    folderpart = "-CrossValidation"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)
    countryId = GetCountryFolderID(service, stateName, folderpart)

    # Define all needed files
    name = 'crossVal'
    years = [1992, 2001, 2004, 2006, 2008, 2011, 2016]

    allNeededFiles = []
    for y in years:
        filename = name + str(y) + ".csv"
        allNeededFiles.append(filename)

    # Get all files within the country's Cross Validation folder.
    if countryId is not None:
        results = service.files().list(q="'{}' in parents".format(countryId),
                                       pageSize=100, fields="nextPageToken, files(id, name)").execute()
        for file in results.get('files', []):
            # Process change
            if file.get('name') in allNeededFiles:
                # CrossValidation File exist, remove from list
                allNeededFiles.remove(file.get('name'))

        if len(allNeededFiles) == 0:
            # All done
            return True
        else:
            return False

# Returns list of filenames and grid cells which are not yet executed
def CheckImageProgress(countryName, gridCells, yearFrom=1984, yearTo=2021, fails=4):
    folderpart = "-Image"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)

    # No grid cells splitted
    if len(gridCells) == 0:
        return []

    # All possible files names
    allFiles = []
    allGridCells = []

    for cell in gridCells:
        for year in range(yearFrom, yearTo):
            #allFiles.append("image-" + str(year) + "-" + countryName + '-' + str(cell[0]) + ".tif")
            allFiles.append(countryName + "-" + "image-" + str(cell[0]) + '-' + str(year) + ".tif")
            subfoldername = countryName + '-Image/' + str(cell[0])
            if subfoldername not in allGridCells:
                allGridCells.append(subfoldername)

    countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is not None:
        results = service.files().list(q="'{}' in parents".format(countryId), pageSize=200, fields="nextPageToken, files(id, name)").execute()

        for file in results.get('files', []):
            # Process change
            if file.get('name') in allGridCells:
                # Get subfiles
                subfiles = service.files().list(q="'{}' in parents".format(file.get('id')), pageSize=200,
                                               fields="nextPageToken, files(id, name)").execute()
                for subfile in subfiles.get('files', []):
                    if subfile.get('name') in allFiles:
                        # Remove file
                        allFiles.remove(subfile.get('name'))

        if len(allFiles) == 0:
            # All done
            return [], []
        else:
            # Return cell names and filenames of not yet executed cells
            cells = []
            for cell in gridCells:
                cellName = str(cell[0])
                # If more than x images per cell are not generated, cell is not finished.
                if sum(1 for s in allFiles if cellName in s) > fails:
                    cells.append(cell[0])

            return cells, allFiles
    else:
        logging.warning("No country image folder in google drive found for country: {}".format(countryName))
        return []

def ManageImageFolders(countryName):
    folderpart = "-Image"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)

    countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is None:
        # TODO create folder
        print("Create drive image-folder for {}".format(countryName))
        foldername = countryName + folderpart
        file_metadata = {
            'name': foldername,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata,
                                      fields='id').execute()
    countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is not None:
        subfolders = GetImageSubFolderIDs(service, countryName, folderpart+"/")
        # Move the file to the new folder
        for subfolder in subfolders:
            print("Move Drive subfolder {} to state image folder".format(subfolder))
            previous_parents = ",".join(subfolder.get('parents'))
            file = service.files().update(fileId=subfolder.get('id'),
                                            addParents=countryId,
                                            removeParents=previous_parents,
                                            fields='id, parents').execute()
            body = service.files().get(fileId=subfolder.get('id')).execute()
            body['name'] = subfolder.get('name').split("/")[1]
            file = service.files().update(fileId=subfolder.get('id'),
                                   body=body).execute()


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

def CreateImageFolder(countryName, gridcell):
    folderpart = "-Image"
    creds = Initialize()
    service = build('drive', 'v3', credentials=creds)

    countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is None:
        print("Create drive image-folder for {}".format(countryName))
        foldername = countryName + folderpart
        file_metadata = {
            'name': foldername,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata,
                                      fields='id').execute()
        countryId = GetCountryFolderID(service, countryName, folderpart)

    if countryId is not None:
        subfoldername = countryName+folderpart+"/"+str(gridcell)
        subfiles = service.files().list(q="'{}' in parents".format(countryId), pageSize=200,
                                        fields="nextPageToken, files(id, name)").execute()
        if subfoldername not in subfiles:
            file_metadata = {
                'name': subfoldername,
                'parents': [countryId],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = service.files().create(body=file_metadata,
                                      fields='id').execute()

if __name__ == '__main__':
    main()