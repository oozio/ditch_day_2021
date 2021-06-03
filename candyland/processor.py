import re
import boto3
import decimal
import json
import random
import requests

import discord_utils

from boto3.dynamodb.conditions import Key
from collections import defaultdict

dynamodb_client = boto3.resource('dynamodb')
table = dynamodb_client.Table("candyland")

INSTRUCTIONS = """
 The not-turn-based race to get to the Red Queen's castle is on! 
 Figure out what color you are,
 and **/candyland roll** to draw a card and move to the corresponding square!!!!
"""


END = [1, -2]
CHANNEL = '845156968528347146'

BACKGROUND_COLOR = "brown"
COLORS = ['orange', 'blue', 'yellow', 'green', 'red', 'purple', 'white_large']
SPECIALS = ['lollipop']
SPECIALS = ['peacock', 'candy', 'fire', 'lollipop', 'nazar_amulet', 'pill', 'soap', 'dolls']

AVAILABLE_COLORS = COLORS.copy()
AVAILABLE_SPECIALS = SPECIALS.copy()

PATHS = {
    (5, 5): [ [-1, 1], [-1, 2], [-2, 2], [-2, 3], [-3, 3] ],
    (20, 11):  [
        [-2, 0], [-2, 1], [-3, 1], [-4, 1], [-5, 1], [-6, 1], [-7, 1], [-8, 1], [-9, 1], [-10, 1], [-11, 1],
        [-11, 2], [-11, 3], [-11, 4], [-11, 5], [-11, 6],
        [-10, 6], [-9, 6], [-9, 5],
        [-8, 5], [-8, 4], [-8, 4], [-7, 4], [-6, 4], [-5, 4], [-5, 3], [-4, 3], [-3, 3], [-2, 3], [-1, 3],
        [-1, 4], [-1, 5], [-1, 6], [-1, 7], [-2, 7], [-3, 7], [-4, 7],
        [-4, 6], [-5, 6], [-6, 6], [-7, 6], [-7, 7], [-7, 8], [-7, 9], 
        [-6, 9], [-5, 9], [-4, 9], [-3, 9], [-2, 9], 
        [-2, 10], [-2, 11], [-3, 11], [-4, 11], [-5, 11], [-5, 12], [-5, 13],
        [-6, 13], [-7, 13], [-8, 13], [-8, 12], [-8, 11], [-8, 10],
        [-9, 10], [-9, 9], [-10, 9], [-11, 9], [-11, 10], [-11, 11],
        [-11, 12], [-10, 12], [-10, 13], [-10, 14], [-10, 15], 
        [-9, 15], [-8, 15], [-7, 15], [-6, 15], [-5, 15], [-4, 15], 
        [-3, 15], [-2, 15], [-1, 15], [-1, 16], [-1, 17], [-1, 18], 
        [-1, 19], [-2, 19], [-3, 19], [-3, 18], [-4, 18], [-5, 18],
        [-6, 18], [-6, 19], [-7, 19], [-8, 19], [-8, 18], [-9, 18], 
        [-10, 18]
        
        ]
}

LEVELS = {
    1: (5, 5),
    2: (20, 11)
}

def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.iterkeys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def draw_card():
    options =  table.get_item(Key={'pkey': 'game_stats'})['Item']['used_colors']
    if n_players_remaining() != 1:
        weights = [8 if x in COLORS else 2 for x in options]
    else:
        weights = [10 if x in COLORS else 1 for x in options]
    result = random.choices(options, weights=weights, k=1)[0]
    print(f'draw card: {result}')
    return result
    
def n_players_remaining():
    players = get_all_players()
    left = 0
    for player_item in players:
        player_id = player_item['pkey']
        player_loc = get_player_loc(player_id)
        
        if player_loc != [0, -2]:
            left += 1
    return left

def get_random_color(colors_only=False):
    global AVAILABLE_COLORS
    global SPECIALS
    if colors_only:
        AVAILABLE_COLORS = COLORS.copy()
        AVAILABLE_COLORS.remove("white_large")
    if len(AVAILABLE_COLORS) < 1:
        if AVAILABLE_SPECIALS:
            special = random.choice(AVAILABLE_SPECIALS)
            AVAILABLE_SPECIALS.remove(special)
            AVAILABLE_COLORS = COLORS.copy()
            return special
        else:
            AVAILABLE_COLORS = COLORS.copy()
    result = random.choice(AVAILABLE_COLORS)
    AVAILABLE_COLORS.remove(result)
    return result

def get_path(width, height):
    return PATHS.get((width, height), [])

def generate_board(width, height):
    board = [[f":{BACKGROUND_COLOR}_square:" for x in range(width)] for y in range(height)]

    for x in range(width):
        board[0][x] = f":{BACKGROUND_COLOR}_square:"            
       
    colored_path = []
    used_colors = set()
    for point in get_path(width, height):
        point_color = get_random_color()
        if point_color in COLORS:
            emoji = f":{point_color}_square:"
        else:
            emoji = f":{point_color}:"
        board[point[0]][point[1]] = emoji
        colored_path.append([point[0], point[1], point_color])
        used_colors.add(point_color)

    # set start and end points
    board[-1][0] = ":black_square_button:"
    board[0][-1] = ":heart_decoration:"
    board[0][-2] = ":european_castle:"
    board[0][-3] = ":heart_decoration:"
    board[1][-2] = ":rainbow_flag:"
    
    
    colored_path.append([1, -2, 'rainbow'])
    colored_path.insert(0, [-1, 0, 'black'])

    return board, colored_path, list(used_colors)

def str_board(board):
    # split in half
    half_way = len(board) // 2
    first_half = '\n'.join([''.join([f'{cell}' for cell in row]) for row in board[:half_way]])
    second_half = '\n'.join([''.join([f'{cell}' for cell in row]) for row in board[half_way:]])
    return first_half, second_half


def get_colored_path():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return replace_decimals(response['Item']['colored_path'])

def init_player(player_id):
    player_color = get_random_color(colors_only=True) 
    player = {'pkey': player_id, 'color': player_color, 'emoji': f':{player_color}_circle:', 'loc': [-1, 0], 'key_type': 'player'}
    table.put_item(Item=player)
    return {'Item': player}

def reset_players():
    for player in get_all_players():
        table.delete_item(Key={'pkey': player['pkey']})

    
def get_player(player_id):
    response = table.get_item(Key={'pkey': player_id})
    return response['Item']

def get_player_loc(player_id):
    response = table.get_item(Key={'pkey': player_id})
    if 'Item' not in response:
        print('initializing player')
        response = init_player(player_id)

    print(response)
    return replace_decimals(response['Item']['loc'])
 

def move(player_id, new_loc):
    x = new_loc[0]
    y = new_loc[1]
    player = get_player(player_id)
    # update in db
    table.update_item(
        Key={'pkey': player_id},
        UpdateExpression="set loc=:s",
        ExpressionAttributeValues={
            ':s': str(new_loc)
            }  
        )
        
    # update board
    board[x][y] = player['emoji']

def find_next_location(current_point, card):
    full_path = get_colored_path()
    if card in COLORS:
        valid_points = full_path[full_path.index(current_point)+1:] 
    else:
        valid_points = full_path
    
    print(f'valid: {valid_points}')
    for point in valid_points:
        if card in point[2] or point[2] == 'rainbow':
            return [point[0], point[1]]

def get_current_level():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return int(response['Item']['game_level'])

def get_game_status():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return response['Item']['game_status']

def end_game():
    if get_game_status() != 'in_progress':
        return
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set game_status=:s",
      ExpressionAttributeValues={
          ':s': 'not_started'
          }  
      )
        
    reset_players() 
      
def reset_game():
    if get_game_status() != 'in_progress':
        return
    level = 0
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set game_status=:s",
      ExpressionAttributeValues={
          ':s': 'not_started'
          }  
      )
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set game_level=:n",
      ExpressionAttributeValues={
          ':n': level
          }  
      )
      
      
    reset_players()

def start_game():
    global AVAILABLE_COLORS
    global AVAILABLE_SPECIALS
    
    AVAILABLE_SPECIALS = SPECIALS.copy()
    AVAILABLE_COLORS = COLORS.copy()
    
    if get_game_status() != 'not_started':
      return

    level = get_current_level() + 1
    width, height = LEVELS.get(level)
    board, path, used_colors = generate_board(width, height)
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set used_colors=:s",
      ExpressionAttributeValues={
          ':s': used_colors
          }  
      )
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set game_status=:s",
      ExpressionAttributeValues={
          ':s': 'in_progress'
          }  
      )
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set board=:s",
      ExpressionAttributeValues={
          ':s': board
          }  
      )

    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set base_board=:s",
      ExpressionAttributeValues={
          ':s': board
          }  
      )

    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set colored_path=:s",
      ExpressionAttributeValues={
          ':s': path
          }  
      )


    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set game_level=:n",
      ExpressionAttributeValues={
          ':n': level
          }  
      )
    
    board_top, board_bottom = str_board(board)
    discord_utils.send_response(CHANNEL, None, {'title': 'Instructions', 'description': INSTRUCTIONS})
    top_msg = json.loads(discord_utils.send_response(CHANNEL, board_top)._content.decode("utf-8")).get('id')
    bot_msg = json.loads(discord_utils.send_response(CHANNEL, board_bottom)._content.decode("utf-8")).get('id')
    
    table.update_item(
      Key={'pkey': 'game_stats'},
      UpdateExpression="set message_ids=:n",
      ExpressionAttributeValues={
          ':n': [top_msg, bot_msg]
          }  
      )

    return level
    
def get_message_ids():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return response['Item']['message_ids']

def get_board():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return response['Item']['board']

def get_color(loc):
    for point in get_colored_path():
        if point[0] == loc[0] and point[1] == loc[1]:
            return point[2]
    return "?"

def get_base_board():
    response = table.get_item(Key={'pkey': 'game_stats'})
    return response['Item']['base_board']

def get_all_players():
    scan_kwargs = {
            'FilterExpression': Key('key_type').eq('player'),
            'ProjectionExpression': "pkey"
        }

    response = table.scan(**scan_kwargs)
    return response['Items']

def update_board():
    board = get_base_board()
    print(board)
    players = get_all_players()
    print(players)
    
    for player_item in players:
        player_id = player_item['pkey']
        player = get_player(player_id)
        player_loc = get_player_loc(player_id)
        player_emoji = player['emoji']
        
        board[player_loc[0]][player_loc[1]] = player_emoji
        
        table.update_item(
          Key={'pkey': 'game_stats'},
          UpdateExpression="set board=:s",
          ExpressionAttributeValues={
              ':s': board
              }  
          )
          
    return board
        
def all_done():
    players = get_all_players()
    for player_item in players:
        player_id = player_item['pkey']
        player_loc = get_player_loc(player_id)
        
        if player_loc != [0, -2]:
            return False
    return True

def turn(user_id):
    if get_game_status() != 'in_progress':
      return "No game in progress!"
    
    player_loc = get_player_loc(user_id)
    if player_loc == [0, -2]:
        raise Exception("You've already reached the end, there's nowhere else to go!!")
    player_color = get_player(user_id)['color']
        
    player_cell_color = get_color(player_loc)
    next_loc = None
    while not next_loc:
        card = draw_card()
        print(card)
        next_loc = find_next_location([player_loc[0], player_loc[1], player_cell_color], card)
        print(next_loc)
        

    table.update_item(
      Key={'pkey': user_id},
      UpdateExpression="set loc=:s",
      ExpressionAttributeValues={
          ':s': next_loc
          }  
      )
          

    emoji = f":{card}:" if card in SPECIALS else f":{card}_square:"
    message = f":{player_color}_circle: drew a {emoji} card" 
    
    new_board = update_board()
    board_top, board_bottom = str_board(new_board)

    message_holders = get_message_ids()
  
    discord_utils.edit_message(CHANNEL, message_holders[0], board_top)
    discord_utils.edit_message(CHANNEL, message_holders[1], board_bottom, embed={'title': 'Last move', 'description': message})
            
    if next_loc == END: 
        message += f"\n:{player_color}_circle: made it to the end!!" 
        next_loc = [0, -2]
        table.update_item(
          Key={'pkey': user_id},
          UpdateExpression="set loc=:s",
          ExpressionAttributeValues={
              ':s': next_loc
              }  
          )
              
        
        new_board = update_board()
        board_top, board_bottom = str_board(new_board)
    
        message_holders = get_message_ids()
      
        discord_utils.edit_message(CHANNEL, message_holders[0], board_top)
        discord_utils.edit_message(CHANNEL, message_holders[1], board_bottom, embed={'title': 'Last move', 'description': message})
                
        if all_done():
            if get_current_level() == 1:
                end_game()
                discord_utils.send_response(CHANNEL, "Looks like everyone's reached the end!", embed={'title': "Now it's time", 'description': 'for a true test of skill!!!'})
                start_game()
                    
            elif get_current_level() == 2:
                end_game()
                discord_utils.send_response(CHANNEL, None, embed={'title': "You made it to the end!!", 'description': "Maybe the Queen will be proud of you? Let's see what she says.."})

    
def _processAdminCommandAndGetMessage(server_id, command):
    everyone_id = server_id # @everyone has same role_id as server_id
    if command == 'start':
        level = start_game()
        return f"Initialized candyland {level}/{len(LEVELS)}"
  
    if command == 'reset':
        reset_game()
        return 'Reset candyland to level 1'
    return 'Input either \"start\" or \"reset\"'
 

def evaluateInput(channel_id, user_id, action):
    channel = discord_utils.get_channel_by_id(channel_id)
    server_id = channel['guild_id']
    channel_name = channel['name']
    if channel_name == 'admin-channel':
        return _processAdminCommandAndGetMessage(server_id, action)
    
    if action == 'roll': 
        return turn(user_id)
    
    if not action:
      # return current level info
        return (f'Available commands:\n"draw"')
