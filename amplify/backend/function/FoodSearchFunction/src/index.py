import json
import urllib3

def handler(event, context):
    # 1. Extract the food name from the frontend request
    # Logic: Look for ?name=apple in the URL
    query_params = event.get('queryStringParameters')
    food_query = query_params.get('name') if query_params else "apple"
    
    print(f"User is searching for: {food_query}")

    # 2. Call the Open Food Facts API (The "External Brain")
    http = urllib3.PoolManager()
    # We limit results to 5 to keep it fast
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_query}&search_simple=1&action=process&json=1&page_size=5"
    
    try:
        response = http.request('GET', url)
        data = json.loads(response.data.decode('utf-8'))
        
        # 3. Clean the data (Map the messy API response to clean fields)
        products = data.get('products', [])
        results = []
        
        for p in products:
            nutrients = p.get('nutriments', {})
            portion = p.get('serving_size')

            results.append({
                "id": p.get('_id'),
                "product_name": p.get('product_name', 'Unknown'),
                "brand": p.get('brands', 'Generic'),
                "image": p.get('image_front_url', ''),
                "portion": portion,
                "calories": nutrients.get('energy-kcal_100g', 0),
                "macros": {
                    "protein": nutrients.get('proteins_100g', 0),
                    "carbs": nutrients.get('carbohydrates_100g', 0),
                    "fat": nutrients.get('fat_100g', 0),
                          }
                    })

        # 4. Return to the React Frontend
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*', # Crucial for browser security
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(results)
        }

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to fetch food data'})
        }