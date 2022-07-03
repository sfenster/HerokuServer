import requests
from dotenv import load_dotenv
import os


load_dotenv()

def add_registrant(action_data, webhook_data):
    auth_url = "https://www.swoogo.com/api/v1/oauth2/token.json"
    b64_key_secret = os.getenv("SWOOGO_B64_KEY_SECRET")
    auth_headers = {'Content-Type':'application/x-www-form-urlencoded', 'Authorization':'Basic ' + b64_key_secret}
    auth_data = {'grant_type':'client_credentials'}


    auth_resp = requests.post(url=auth_url, headers=auth_headers, data=auth_data).json()
    #resp_dict = auth_resp.json()

    req_url = "https://www.swoogo.com/api/v1/registrants/create.json"
    req_headers = {"Authorization": f"Bearer {auth_resp['access_token']}"}

    req_data = {}

    for key in webhook_data:
        if key == 'event_id': req_data[key] = webhook_data[key]
        if key == 'email': req_data[key] = webhook_data[key]
        if key == 'first_name': req_data[key] = webhook_data[key]
        if key == 'last_name': req_data[key] = webhook_data[key]
        if key == 'registration_status': req_data[key] = webhook_data[key]
        if key == 'po_number': req_data[key] = webhook_data[key]
        if key == 'discount_code': req_data[key] = webhook_data[key]
        if key == 'payment_method': req_data[key] = webhook_data[key]
        if key == 'send_email': req_data[key] = webhook_data[key]


    response = requests.post(url=req_url, headers=req_headers, data=req_data).json()


    #print(f"access token = {auth_resp['access_token']}")
    #print(f"Newly created id for {response['email']} is {response['id']}.")
    if 'status' in response:
        print(f"ERROR: {response['message']}")

    return response
