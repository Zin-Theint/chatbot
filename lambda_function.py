import json
import os
import uuid
import boto3
import urllib.request
import urllib.error
from datetime import datetime

def lambda_handler(event, context):

    weather_api_key = os.environ["OPENWEATHER_API_KEY"]
    logs_table_name = os.environ["LOGS_TABLE_NAME"]

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(logs_table_name)

    # Parse the request body safely
    body = event.get('body', '{}')

    if isinstance(body, str):
        body = json.loads(body)  # Only parse if it's a string

    user_query = body.get('query', '').lower()

    # Decide action
    if 'weather' in user_query:
        city = extract_city(user_query)
        result = get_weather_info(city, weather_api_key)
    elif 'joke' in user_query:
        result = get_random_joke()
    else:
        result = "I can tell you the weather or a joke! Try asking about weather or jokes."

    # Log to DynamoDB
    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    table.put_item(
        Item={
            'RequestId': request_id,
            'Query': user_query,
            'Response': result,
            'Timestamp': timestamp
        }
    )

    # Return response
    response_body = {
        'requestId': request_id,
        'response': result
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body),
        'headers': {
            'Content-Type': 'application/json'
        }
    }


def extract_city(user_query):
   
    words = user_query.split()
    if 'in' in words:
        idx = words.index('in')
        if idx + 1 < len(words):
            return words[idx + 1]
    return "New York"

def get_weather_info(city, api_key):
   
    base_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        with urllib.request.urlopen(base_url) as response:
            data = json.loads(response.read())
            if response.status == 200:
                city_name = data['name']
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"The weather in {city_name} is {temp}°C with {desc}."
            else:
                return "Sorry, I couldn't get the weather right now."
    except urllib.error.URLError as e:
        return f"Error fetching weather data: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_random_joke():
   
    req = urllib.request.Request(
        url="https://icanhazdadjoke.com/",
        headers = {
                    "Accept": "application/json",
                    "User-Agent": "AWS Lambda Chatbot (test@example.com)"
                }
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data.get('joke', "Hmm, I couldn't find a joke right now!")
    except urllib.error.URLError as e:
        return f"Error fetching a joke: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"