import json
import boto3
import uuid
import os
from decimal import Decimal  # <--- Add this!

# Use the environment variable
TABLE_NAME = os.environ.get('STORAGE_FOODTABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        if 'body' in event and event['body']:
            body = json.loads(event['body'])
        else:
            body = event
            
        # Use Decimal(str()) to safely convert inputs to DynamoDB-friendly numbers
        food_item = {
            'foodId': str(uuid.uuid4()),
            'source': 'USER',
            'product_name': str(body.get('name', 'Custom Food')).lower().strip(),
            'brand': str(body.get('brand', 'Generic')).lower().strip(),
            'calories': Decimal(str(body.get('calories', 0))),
            'macros': {
                'protein': Decimal(str(body.get('protein', 0))),
                'carbs': Decimal(str(body.get('carbs', 0))),
                'fat': Decimal(str(body.get('fat', 0)))
            },
            'portion': str(body.get('portion', '1 serving')),
            'isPublic': True
        }
        
        table.put_item(Item=food_item)
        
        # Note: json.dumps doesn't know how to handle Decimal, 
        # but since we are returning a simple message, this is fine.
        return {
            'statusCode': 201,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({'message': 'Success!', 'id': food_item['foodId']})
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }