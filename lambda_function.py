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
        guess = discord_utils.get_input(data, "guess")
        output = hare.processor.evaluateInput(channel_id, guess)
        return discord_utils.format_response('MESSAGE_WITH_SOURCE', output)

    # vvv TEMP (REMOVE) vvv
    if command == "channel-test":
        arg = discord_utils.get_input(data, "arg")
        if arg:
          return discord_utils.format_response('MESSAGE_WITH_SOURCE', str(arg.encode()))
        return discord_utils.format_response('MESSAGE_WITH_SOURCE', channel_id)
    # ^^^ TEMP (REMOVE) ^^^

    return discord_utils.format_response('MESSAGE_WITH_SOURCE', "didn't recognize command!! run away!!!")
    
    
