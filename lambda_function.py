from botocore.exceptions import ClientError
from IPython.display import HTML
from datetime import datetime
import pandas
import numpy
import boto3
import sys
import os

def check_for_duplicates (errors_list):
    # This function finds if any duplicate exists or not.
    duplicate_list = []
    unique_list = []

    for error in errors_list:
        if error not in unique_list:
            unique_list.append(error)
        elif error not in duplicate_list:
            duplicate_list.append(error)
    
    return duplicate_list

def upload_file_to_s3(file_content, file_name, bucket, content_value):
    # This function uploads the HTML file to S3 bucket.
    s3_client = boto3.client('s3')

    try:
        response = s3_client.put_object(Body=file_content, Key=file_name, Bucket=bucket, ContentType=content_value)
    except ClientError as response:
        return response
    
    return response

def download_file_from_s3(file_name, bucket, object_name=None):
    # This function uploads the HTML file to S3 bucket.
    s3_client = boto3.client('s3')

    try:
        response = s3_client.download_file(bucket, object_name, file_name)
    except ClientError as response:
        return response
    
    return response

def lambda_handler(event, context):
    # Main function.
    try:
        if os.getenv('ONLINE_CODE') is None or os.getenv('BATCH_CODE') is None or os.getenv('ERROR_DESCRIPTION') is None:
            raise Exception('Environment variables are empty')
    except Exception as error_code:
        return str(error_code)

    bucket_name = 'error-narrative-sheet'

    if __name__ == 'lambda_function':
        os.chdir('/tmp')
        sys.path.append('/tmp')

    download_file_from_s3('error_narrative_sheet.py', bucket_name, 'error_narrative_sheet.py')
    
    from error_narrative_sheet import error_codes_list

    error_codes_list.append(
        [   os.getenv('ONLINE_CODE'),
            os.getenv('BATCH_CODE'), 
            os.getenv('ERROR_DESCRIPTION')
        ]
    )

    online_errors = []
    batch_errors = []

    for error_codes_line in error_codes_list:
        online_errors.append(error_codes_line[0])
    
    for error_codes_line in error_codes_list:
        batch_errors.append(error_codes_line[1])
    
    headers = ['Online Error Code', 'Batch Error Code', 'Error Description']

    try:
        if check_for_duplicates(online_errors) == [] or check_for_duplicates(batch_errors) == []:

            df = pandas.DataFrame(error_codes_list)
            pandas.set_option('display.colheader_justify', 'center')
            df.index = numpy.arange(1, len(df) + 1)
            df.columns = headers
            df = df.rename_axis(columns='Serial Number')
            error_narrative_table = df.to_html()
            
            updated_error_codes = f'error_codes_list = {error_codes_list}'
            
            files_to_upload = {
                'error_narrative_sheet.html': 'text/html',
                'error_narrative_sheet.py': 'text/x-python-script'
            }
            
            try:
                for file_name, content_type in files_to_upload.items():
                    if file_name == 'error_narrative_sheet.html':
                        upload_file_to_s3(error_narrative_table, file_name, bucket_name, content_type)
                    elif file_name == 'error_narrative_sheet.py':
                        upload_file_to_s3(updated_error_codes, file_name, bucket_name, content_type)
            finally:
                    current_time = datetime.now()
                    return f'Program completed at {current_time.strftime("%d/%m/%Y %H:%M:%S")}'
        else:
            raise Exception('Duplicates present in Online / Batch errors')
        
    except Exception as error_code:
        return str(error_code)

if __name__ == "__main__":
    lambda_handler(event=None, context=None)
