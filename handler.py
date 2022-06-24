import json
import requests
from flask import jsonify
from pathlib import Path
from actions import swoogo_api

#HANDLER.RUN_ACTIONS will be the job enqueued in all cases.
#RUN_ACTIONS will be passed both the webhook info and action step info, and determine which APIs to call

def run_actions(action, webhook_data):
    #Parse the json passed in the parameter for the action and the webhook data, call appropriate function below
    #e.g., run_add_registrant_action()

    if action['type'] == "registration":
        resp = run_add_registrant_action(action['action_data'], webhook_data)


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": {"action" : action, "webhook_data": webhook_data, "auth":resp},
    }

def run_add_registrant_action(action_data, webhook_data):
    #Use passed data to determine whose APIs to call, then add registrant.
    if action_data['platform']=='swoogo':
        resp = swoogo_api.add_registrant(action_data, webhook_data)
    else:
        resp = "No add registrant action found"
    return resp
