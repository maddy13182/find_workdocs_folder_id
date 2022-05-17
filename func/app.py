import json
import boto3
import logging
import os
logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('workdocs')
dynamodb = boto3.resource('dynamodb')
ddbtable = os.environ['DDBtable']


def writetoddb(Folderid,FolderName,ParentFolderId):
    table = dynamodb.Table(ddbtable)
    table.put_item(Item={
        'FolderId': Folderid,
        'ParentFolderID':ParentFolderId,
        'FolderName': FolderName
    })

    
def createFolderEvent(ParentFolderId,FolderName):
    marker = None
    while True:
        logger.info('starting while loop')
        paginator = client.get_paginator('describe_folder_contents')
        response_iterator = paginator.paginate(
                FolderId=ParentFolderId,
                Sort='DATE',
                Order='DESCENDING',
                Type='FOLDER',
                PaginationConfig={
                    'PageSize': 2,
                    'StartingToken': marker})
       
        for page in response_iterator:
            logger.info('page is %s ', page)
            for count in range(len(page['Folders'])):
                logger.info ('value of count is %s ', count)
                logger.info(page['Folders'][count])
                if page['Folders'][count]['Name'] == FolderName:
                    FolderId= page['Folders'][count]['Id']
                    print ('found the folder',page['Folders'][count]['Id'])
                    FolderName = page['Folders'][count]['Name'] 
                    ParentFolderId = page['Folders'][count]['ParentFolderId'] 
                    writetoddb(FolderId,FolderName,ParentFolderId)
                    return {
                        "statusCode": 200,
                        "body": json.dumps(
                        {
                        "Message": "updated DDB table with folderID"
                        }
                            ),
                        }
                    
            try:
                marker = page['Marker']
            except KeyError:
                break

def updateFolderEvent(FolderId,FolderName):
    response = client.get_folder(
                FolderId= FolderId,
                IncludeCustomMetadata=False
                )
    FolderName = response['Metadata']['Name'] 
    ParentFolderId = response['Metadata']['ParentFolderId']
    writetoddb(FolderId,FolderName,ParentFolderId)

def lambda_handler(event, context):
    
    print(event)
    if event['detail']['eventName'] == "CreateFolder":
        logger.info('Create folder event workflow')
        try:
            FolderName=event['detail']['requestParameters']['FolderName']
            ParentFolderId=event['detail']['requestParameters']['ParentFolderId']
            createFolderEvent(ParentFolderId,FolderName)
        except KeyError:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": "New folder from explorer created, will be handled by update action"
                    }
                ),
            }
    
    elif event['detail']['eventName'] == "UpdateFolder":
        FolderName=event['detail']['requestParameters']['Name']
        FolderId=event['detail']['requestParameters']['FolderId']
        updateFolderEvent(FolderId,FolderName)
         
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "issue with the input event received"
                }
                )
                }
