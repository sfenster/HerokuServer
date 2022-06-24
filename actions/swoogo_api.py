import requests

def add_registrant(action_data, webhook_data):
    auth_url = "https://www.swoogo.com/api/v1/oauth2/token.json"
    b64_key_secret = "UlR3TTJ5SlRDTjFCaWg5bmxLcEhoOnY3NDJkWVk5d1BKbGVrU2d2VlJZSmFQYTBoWGNsdkdpZnZCcElBREdKcA=="
    auth_headers = {'Content-Type':'application/x-www-form-urlencoded', 'Authorization':'Basic ' + b64_key_secret}
    auth_data = {'grant_type':'client_credentials'}

    auth_resp = requests.post(url=auth_url, headers=auth_headers, data=auth_data).json()
    #resp_dict = auth_resp.json()
    print(f"access token = {auth_resp['access_token']}")
    return auth_resp
