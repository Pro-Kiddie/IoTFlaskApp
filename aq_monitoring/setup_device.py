import json, boto3, botocore
from models import Device, Status
from pynamodb.exceptions import PutError
from botocore.client import ClientError

# Read Config file
with open("config.json", "r") as config_file:
    config = json.load(config_file)

    # Setup dynamo db for the device
    try:
        # Register itself under Device table
        device = Device(config.get("device_id"))
        device.save(~Device.device_id.exists())
        print("Registered under Device Table.")
        # Populate components' status in Status table
        components = config.get("device_components")
        for k in components.keys():
            Status(device.device_id + "_" + k, status=components[k]).save(~Status.device_comp.exists())
        print("Registered device's component status under Status table")
    except PutError as e:
        if isinstance(e.cause, ClientError):
            code = e.cause.response['Error'].get('Code')
            if code == "ConditionalCheckFailedException":
                print("IoT device has already been registered with the relevant tables.")