import json
import time
import os
import boto3
from datetime import datetime
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import logging

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    
def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
    
def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def validate_category(slots):
    c1 = slots['category']
    c2 = slots['categoryTwo']
    return build_validation_result(True, None, None)
    
def searchIntent(intent_request):
    c1 = intent_request['currentIntent']['slots']['category']
    c2 = intent_request['currentIntent']['slots']['categoryTwo']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    records = json.dumps({
        'category': c1,
        'categoryTwo': c2
    })
    
    session_attributes['currentReservation'] = records
    
    if intent_request['invocationSource'] == 'DialogCodeHook':
        
        validation_result = validate_category(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        #session_attributes['currentReservation'] = records
        #return delegate(session_attributes, intent_request['currentIntent']['slots'])

    #logger.debug('bookHotel under={}'.format(reservation))
    session_attributes['lastConfirmedReservation'] = records
    category = []
    if c1 is not None:
        category.append(c1.lower())
    if c2 is not None:
        category.append(c2.lower())
    
    print(category)
    result = searchPhotos(category)
    #print(result)
    photos = []
    for i in result:
        photo=i["_source"]["objectKey"]
        #print(photo)
        bucket=i["_source"]["bucket"]
        url = "https://"+bucket+".s3.amazonaws.com/"+photo
        #print(url)
        photos.append(url)
    print(",".join(photos))
    msg = ",".join(photos)
    #print(type(msg))
    #print(msg)
    if msg == "":
        msg = "Not Found!"
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': msg
        }
    )

def searchPhotos(category):
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
    
    condition = {"from":0, "size":100, "query": {"terms": {'labels': category}}}
    
    #condition = {"query" : {"match_all": {"terms": {'labels': category}}}}
    result = es.search(index="photo", doc_type="_doc", body=condition)
    #print(result['hits']['hits'])
    return result['hits']['hits']
    
def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    print(event)
    if 'currentIntent' in event:
        intent_name = event['currentIntent']['name']
        print(intent_name)
        return searchIntent(event)
    else:
        query = event["queryStringParameters"]["q"]
        client = boto3.client('lex-runtime')
        response = client.post_text(
            botName='SearchPhoto', 
            botAlias='BETA', 
            userId='user', 
            sessionAttributes={},
            requestAttributes={},
            inputText=query)
        print(response['message'])
        return {
            'headers':{
                'Access-Control-Allow-Origin': '*'
            },
            'statusCode': 200,
            'body': response['message']
        }
