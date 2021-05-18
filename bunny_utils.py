import boto3

from boto3.dynamodb.conditions import Key
dynamodb_client = boto3.resource('dynamodb')

table = dynamodb_client.Table("bunnies")

CAUGHT = 'caught'
SCAMPERING = 'scampering'
HIDING = 'hiding'

LOCATION = 'bunny_location'
STATUS = 'bunny_status'

# functions:
#  populate_rooms(rooms (list))
#  show_all_bunnies()
#  catch_bunny(1)
#  hide_all_bunnies()
#  exterminate()

# statuses: hiding, caught, scampering

def get_bunnies(location=None, status=''):
    if location:
        response = table.get_item(Key={LOCATION: str(location)})
        print(response)
        return [response['Item']]
    elif status:
        scan_kwargs = {
            'FilterExpression': Key(STATUS).eq(status),
            'ProjectionExpression': LOCATION
        }

        response = table.scan(**scan_kwargs)
        print(response)

        return response['Items']
    else:
        return table.scan()['Items']

def exterminate():
    for bunny in get_bunnies():
        table.delete_item(Key={LOCATION: bunny[LOCATION]})

def populate_rooms(rooms):
    for room in rooms:
        bunny = {STATUS: HIDING, LOCATION: str(room)}
        table.put_item(Item=bunny)

def hide_all_bunnies():
    for bunny in get_bunnies():
        # if bunny['bunny_status'] != 'caught':
        table.update_item(
            Key={LOCATION: bunny[LOCATION]},
            UpdateExpression=f"set {STATUS}=:s",
            ExpressionAttributeValues={
                ':s': HIDING
                }
            )

def show_all_bunnies():
    for bunny in get_bunnies():
        if bunny[STATUS] != CAUGHT:
            table.update_item(
                Key={LOCATION: bunny[LOCATION]},
                UpdateExpression=f"set {STATUS}=:s",
                ExpressionAttributeValues={
                    ':s': SCAMPERING
                    }
                )

def catch_bunny(room):
    for bunny in get_bunny(location=room):
        table.update_item(
            Key={LOCATION: bunny[LOCATION]},
            UpdateExpression=f"set {STATUS}=:s",
            ExpressionAttributeValues={
                ':s': CAUGHT
                }
            )
