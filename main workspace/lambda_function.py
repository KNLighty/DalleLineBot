import json
import urllib.request
import os
from io import BytesIO
import boto3
from PIL import Image # type: ignore
from deep_translator import GoogleTranslator

STANDARD_LINE_HEADER = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
}

# This is the main function that AWS Lambda will invoke when the function is triggered
def lambda_handler(event, context):
    # Iterate over each message event in the received payload
    for message_event in json.loads(event['body'])['events']:
        start_loading_animation(message_event['source']['userId'])

        user_response = message_event['message']['text']
        user_response_en_translation = translate_to_english(user_response)
        
        # Generate response from DALL-E
        response = generate(user_response_en_translation)
        # URL for the generated image
        response_url = response['data'][0]['url'] 
        
        # Send generated image as reply to the user
        send_image_reply(message_event, response_url)
        
    # Returning a response indicating successful execution
    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }


def start_loading_animation(user_id):
    url_loading_animation = 'https://api.line.me/v2/bot/chat/loading/start'
    
    headers = STANDARD_LINE_HEADER
        
    body = {
        "chatId": user_id,
        "loadingSeconds": 10
    }
    
    req = urllib.request.Request(url_loading_animation, data=json.dumps(body).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(req) as res:
        pass
    

def generate(message):
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    URL = 'https://api.openai.com/v1/images/generations'

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = json.dumps({'prompt': message}).encode('utf-8')
    req = urllib.request.Request(URL, data=data, headers=headers)
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result
    
    return "NO DATA"


def send_image_reply(message_event, image_url):
    # URL for the LINE Messaging API - reply
    url_message_reply = 'https://api.line.me/v2/bot/message/reply'
        
    headers = STANDARD_LINE_HEADER
        
    body = {
        'replyToken': message_event['replyToken'],
        'messages': [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        ]
    }

    req = urllib.request.Request(url_message_reply, data=json.dumps(body).encode('utf-8'), method='POST', headers=headers)
    with urllib.request.urlopen(req) as res:
        pass


def translate_to_english(original_text):
    return GoogleTranslator(source='auto', target='en').translate(original_text)