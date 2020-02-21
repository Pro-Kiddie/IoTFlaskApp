import json
from twilio.rest import Client

# Adjust the Basic Timeout settings to 8 seconds instead of 3.
# Quite slow to connect to twilio api and results in Lambda to timeout
# AWS will try to reinvoke the lambda, resulting in multiple sms sent.

# No specific permission needed
def lambda_handler(event, context):
    twilio_account_sid = ""
    twilio_auth_token = ""
    twilio_my_hp = "" # Can retrieve from database the different numbers to send sms
    twilio_hp = ""
    client = Client(twilio_account_sid, twilio_auth_token)

    device_id = event["device_id"]
    pm_25 = event["pm_25"]
    pm_10 = event["pm_10"]

    sms = "Unhealthy air quality observed at {}.\nPlease investigate!\nPM2.5: {:.1f}\nPM10: {:.1f}".format(device_id, pm_25, pm_10)
    client.api.account.messages.create(to=twilio_my_hp, from_=twilio_hp, body=sms)