import json
import boto3
import requests

import discord_utils
import time_calculator
import hare.processor


def lambda_handler(event, context):
    pong = discord_utils.check_input(event)
    if pong: 
        return pong
    
    body = event["body-json"]
    data = body["data"]
    channel_id = body["channel_id"]
    
    command = data['name']

    # add commands here; use discord_utils.get_input(data, <option name>) to access command input
    
    if command == "calculate-time":
        input = discord_utils.get_input(data, "time_string")
        content = time_calculator.evaluate(input)
        return discord_utils.format_response('MESSAGE_WITH_SOURCE', content)
        
    if command == "hare-puzzle":
        level_code = discord_utils.get_input(data, "level_code")
        guess = discord_utils.get_input(data, "guess")
        output = hare.processor.evaluateInput(level_code, guess)
        return discord_utils.format_response('MESSAGE_WITH_SOURCE', output)

    if command == "channel-test":
        return discord_utils.format_response('MESSAGE_WITH_SOURCE', channel_id)

    return discord_utils.format_response('MESSAGE_WITH_SOURCE', "didn't recognize command!! run away!!!")
    
    
