import json
import boto3
import requests

import discord_utils

LAMBDA = boto3.client('lambda')
API_CALLER = "discord_event_processor"

def invoke_processor(body)
    response = LAMBDA.invoke(
        FunctionName=API_CALLER,
        InvocationType='Event',
        Payload=bytes(json.dumps(body), 'utf-8')
    )

def lambda_handler(event, context):
    # handle discord's integrity check
    pong = discord_utils.check_input(event)
    if pong: 
        return pong
    
    # pass event to processor
    invoke_processor(event)
    
    # return :thinking:
    return discord_utils.format_response('ACK_WITH_SOURCE')
