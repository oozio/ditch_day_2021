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
        
    if command == "hares-request":
        guess = discord_utils.get_input(data, "guess")
        return hare.processor.evaluateInput(channel_id, guess)

    if command == "whistle":
        return garden.processor.evaluateWhistleInput(channel_id)

    if command == "catch":
        return garden.processor.evaluateCatchInput(channel_id)

    if command == "consume":
        substance = discord_utils.get_input(data, "substance")
        return garden.processor.evaluateConsumeInput(channel_id, user_id, substance, role_ids)

    return f"Didn't recognize command {command}!! run away!!"

def lambda_handler(event, context):
    pong = discord_utils.check_input(event)
    if pong: 
        return pong
    
    body = event["body-json"]
    channel_id = body["channel_id"]
    application_id = body["application_id"]
    interaction_token = body["token"]
    command = body['data']['name']
    
    output = "? something broke"
    # get interaction metadata
    try:
        output = handle_command(body)
    except Exception as e:
        discord_utils.delete_response(application_id, interaction_token)
        discord_utils.send_followup(application_id, interaction_token, f"Error: {e}", ephemeral=True)
        raise e
  
    if not output:
        discord_utils.delete_response(application_id, interaction_token)
    else:
        discord_utils.update_response(application_id, interaction_token, output)
        discord_utils.send_response(channel_id, None, {'title': f'/{command}', 'description': output})
