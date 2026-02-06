import json
import urllib3
import boto3
import os
from boto3.dynamodb.conditions import Attr

# Initialize DynamoDB
TABLE_NAME = os.environ.get('STORAGE_FOODTABLE_NAME')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    q_params = event.get('queryStringParameters') or {}
    food_query = q_params.get('name') or "" 
    food_query = food_query.lower().strip()
    #print(f"DEBUG: Searching for string: '{food_query}'") # Check logs for this!
    
    results = []

    # 2. SEARCH INTERNAL DYNAMODB
    if food_query: # Don't scan if query is empty
        try:
            # Let's check what the first item in the DB actually looks like
            #debug_scan = table.scan(Limit=1)
            #print(f"DEBUG: Sample DB Item: {debug_scan.get('Items')}")

            db_response = table.scan(
                FilterExpression=Attr('product_name').contains(food_query)
            )
            
            db_items = db_response.get('Items', [])
            #print(f"DEBUG: Found {len(db_items)} items in DB")

            for item in db_items:
                item['source_type'] = 'INTERNAL'
                results.append(item)
        except Exception as e:
            print(f"DynamoDB Error: {str(e)}")

        # 2. SEARCH OPEN FOOD FACTS API
        http = urllib3.PoolManager()
        # We use a limit of 10 to keep the response snappy
        off_url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_query}&search_simple=1&action=process&json=1&page_size=10"
        
        try:
            api_res = http.request('GET', off_url)
            data = json.loads(api_res.data.decode('utf-8'))
            
            for p in data.get('products', []):
                nutrients = p.get('nutriments', {})
                
                # Map OFF data to match your internal app structure
                results.append({
                    "foodId": p.get('_id'),
                    "source_type": "EXTERNAL",
                    "product_name": p.get('product_name', 'Unknown'),
                    "brand": p.get('brands', 'Generic'),
                    "image": p.get('image_front_url', ''),
                    "calories": nutrients.get('energy-kcal_100g', 0),
                    "macros": {
                        "protein": nutrients.get('proteins_100g', 0),
                        "carbs": nutrients.get('carbohydrates_100g', 0),
                        "fat": nutrients.get('fat_100g', 0),
                    }
                })
        except Exception as e:
            print(f"OFF API Error: {str(e)}")

    # 3. RETURN COMBINED LIST
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(results, default=str)
    }