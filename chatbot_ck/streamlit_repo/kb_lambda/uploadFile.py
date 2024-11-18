import logging
import boto3
from botocore.exceptions import ClientError
import os
import json
import boto3    
from datetime import datetime
from utils.constants import *

def upload_json_data(json_data, sessionID, bucket_name, object_name=None):
    """Upload a file json_data to an S3 bucket
    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    s3 = boto3.resource('s3')
    s3object = s3.Object(f'{bucket_name}', f"{account_id}_{sessionID}.json")
    try:
        s3object.put(
            Body=(bytes(json.dumps(json_data).encode('UTF-8')))
        )
    except ClientError as e:
        logging.error(e)
        return False
    return True

# def upload_file(file_name, sessionID, bucket_name, object_name=None):

# # # Print results.
# # for row in df.itertuples():
# #     st.write(f"{row.Owner} has a :{row.Pet}:")