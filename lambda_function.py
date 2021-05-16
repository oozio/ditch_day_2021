import json
import boto3
import requests

import discord_utils
import time_calculator
import hare.processor
import garden.processor


def handle_command(body):
    # get interaction metadata
    channel_id = body["channel_id"]
    server_id = body["guild_id"]
    user_id = body['member']['user']['id']
    role_ids = body['member']['roles']
    
    data = body['data']
    command = data['name']
    
    # add commands here; use discord_utils.get_input(data, <option name>) to access command input
    if command == "calculate-time":
        input = discord_utils.get_input(data, "time_string")
        return time_calculator.evaluate(input)
        
    if command == "hare-puzzle":
        guess = discord_utils.get_input(data, "guess")
        return hare.processor.evaluateInput(channel_id, guess)

    if command == "consume":
        substance = discord_utils.get_input(data, "substance")
        # old_size = discord_utils.get_size_role(server_id, role_ids)
        # new_size = "Size 11"
        # discord_utils.change_role(server_id, user_id, old_size, new_size)
        return garden.processor.evaluateInput(channel_id, user_id, substance, role_ids)

    # vvv TEMP (REMOVE) vvv
    if command == "channel-test":
        arg = discord_utils.get_input(data, "arg")
        if arg:
          return str(arg.encode())
        return channel_id
    # ^^^ TEMP (REMOVE) ^^^

    return f"Didn't recognize command {command}!! run away!!"

def lambda_handler(event, context):
    pong = discord_utils.check_input(event)
    if pong: 
        return pong
    
    body = event["body-json"]
    application_id = body["application_id"]
    interaction_token = body["token"]
    
    output = "? something broke"
    # get interaction metadata
    try:
        output = handle_command(body)
    except Exception as e:
        discord_utils.delete_response(application_id, interaction_token)
        discord_utils.send_followup(application_id, interaction_token, f"Error: {e}", ephemeral=True)
        raise e
    
    discord_utils.update_response(application_id, interaction_token, output)
