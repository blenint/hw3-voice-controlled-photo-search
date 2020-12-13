import json
import boto3
from datetime import datetime
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

def lambda_handler(event, context):
    # TODO implement
    print(event)
    photo = event['Records'][0]['s3']['object']['key']
    print(photo)
    bucket = "assignment3-b2"
    print(bucket)
    labels=detect_labels(photo, bucket)
    print(labels)
    record= {
        'objectKey':photo,
        'bucket':bucket,
        'createdTimestamp':str(datetime.now()),
        'labels':labels
    }
    
    access_key_id="AKIAUM7QK3PKXXIDYNHI"
    secret_access_key="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"
    credentials = boto3.Session(aws_access_key_id = access_key_id, aws_secret_access_key = secret_access_key).get_credentials()
    region = 'us-east-1'
    service = 'es'
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = "search-a3-photos-h4aokbh5224klt3ozgsbb4pfri.us-east-1.es.amazonaws.com"
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection)
    es.index(index = "photo", doc_type = "_doc", id = photo, body = record)
    
    #condition = {"query": {"terms": {'labels': ['animal']}}}
    #condition = {"query" : {"match_all": {}}}
    #result = es.search(index="photo", doc_type="_doc", body=condition)
    #print(result)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def detect_labels(photo, bucket):
    labels = []
    client=boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}}, MaxLabels=20, MinConfidence=80)
    for label in response['Labels']:
        #print ("Label: " + label['Name'])
        labels.append(label['Name'])
        
    return labels
