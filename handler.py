import json
import requests
from pathlib import Path
from actions.swoogo_api import add_registrant

#HANDLER.RUN_ACTIONS will be the job enqueued in all cases.
#RUN_ACTIONS will be passed both the webhook info and action step info, and determine which APIs to call

def run_actions(action, webhook_data):
    #Parse the json passed in the parameter for the action and the webhook data, call appropriate function below
    #e.g., run_add_registrant_action()

    if action['type'] == "registration":
        run_add_registrant_action(action['action_data'], webhook_data)


    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": {"action" : action, "webhook_data": webhook_data, },
    }

def run_add_registrant_action(action_data, webhook_data):
    #Use passed data to determine whose APIs to call, then add registrant.
    pass
