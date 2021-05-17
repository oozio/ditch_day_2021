import boto3

from boto3.dynamodb.conditions import Key
dynamodb_client = boto3.resource('dynamodb')

table = dynamodb_client.Table("bunnies")

# functions:
#  populate_rooms(rooms (list))
#  show_all_bunnies()
#  catch_bunny(1)
#  hide_all_bunnies()
#  exterminate()

# statuses: hiding, caught, scampering

def get_all_bunnies():
    return table.scan()['Items']

def get_all_caught_bunnies():
    return get_bunny(status='caught')
    
def get_bunny(location=None, status=''):
    if location:
        response = table.get_item(Key={'bunny_location': str(location)})
        print(response)
        return [response['Item']]
    elif status:
        scan_kwargs = {
            'FilterExpression': Key('bunny_status').eq(status),
            'ProjectionExpression': "bunny_location"
        }

        response = table.scan(**scan_kwargs)
        print(response)

        return response['Items']
    
def exterminate():
    for bunny in get_all_bunnies():
        table.delete_item(Key={'bunny_location': bunny['bunny_location']})

def populate_rooms(rooms):
    for room in rooms:
        bunny = {'bunny_status': 'hiding', 'bunny_location': str(room)}    
        table.put_item(Item=bunny)
            
def hide_all_bunnies():
    for bunny in get_all_bunnies():
        # if bunny['bunny_status'] != 'caught':
        table.update_item(
            Key={'bunny_location': bunny['bunny_location']},
            UpdateExpression="set bunny_status=:s",
            ExpressionAttributeValues={
                ':s': 'hiding'
                }  
            )
    
def show_all_bunnies():
    for bunny in get_all_bunnies():
        if bunny['bunny_status'] != 'caught':
            table.update_item(
                Key={'bunny_location': bunny['bunny_location']},
                UpdateExpression="set bunny_status=:s",
                ExpressionAttributeValues={
                    ':s': 'scampering'
                    }  
                )
            
def catch_bunny(room):
    for bunny in get_bunny(location=room):
        table.update_item(
            Key={'bunny_location': bunny['bunny_location']},
            UpdateExpression="set bunny_status=:s",
            ExpressionAttributeValues={
                ':s': 'caught'
                }  
            )
            
