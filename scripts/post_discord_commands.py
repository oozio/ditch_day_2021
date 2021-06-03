import boto3
import json
import requests


from time import sleep
s3 = boto3.client("s3")
ssm = boto3.client('ssm', region_name='us-east-2')


APPLICATION_ID = ssm.get_parameter(Name="/discord/application_id", WithDecryption=True)['Parameter']['Value']
TEST_SERVER_ID = ssm.get_parameter(Name="/discord/server_id", WithDecryption=True)['Parameter']['Value']
BUCKET = 'ditch-day-2021'
KEY = 'commands.json'
BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token", WithDecryption=True)['Parameter']['Value']

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}

global_url = f"https://discord.com/api/v8/applications/{APPLICATION_ID}/commands"
guild_urls = [f"https://discord.com/api/v8/applications/{APPLICATION_ID}/guilds/{TEST_SERVER_ID}/commands"]


def get_json(bucket, key):
    result = s3.get_object(Bucket=bucket, Key=key) 
    text = result["Body"].read().decode()
    return json.loads(text)


def publish_command(url, commands):
    r = requests.post(url, headers=HEADERS, json=commands)
    if r.status_code != 200:
        sleep(20)
        print("retrying once")
        r = requests.post(url, headers=HEADERS, json=commands)
        
    print(r.text)


def get_all_commands(url):
    return requests.get(url, headers=HEADERS).json()
    
def delete_command(url):
    r = requests.delete(url, headers=HEADERS)
    print(r.text)
    
def lambda_handler(event, context):
    for guild_url in guild_urls:
        for command in get_all_commands(guild_url):
            delete_command(f"{guild_url}/{command['id']}")
        
    commands = get_json(BUCKET, KEY)

    for url in guild_urls:
        for command in commands[::-1]:
            publish_command(url, command)
