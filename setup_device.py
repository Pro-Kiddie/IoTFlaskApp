import json, boto3, botocore
from models import Device, Status
from pynamodb.exceptions import PutError
from botocore.client import ClientError

# Read Config file
with open("config.json", "r") as config_file:
    config = json.load(config_file)

    # Setup dynamo db for this device
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

    # Tries to create the s3 bucket if it does not exists
    try:
        s3 = boto3.client("s3")
        bucket = config.get("aws_s3_bucket")
        s3.create_bucket(Bucket=bucket) # By default, the bucket is created in the US East (N. Virginia) Region
        s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={ # Block public access to s3 bucket
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
            }
        )
        print("The S3 bucket to store AQ images have been created.")
    except botocore.exceptions.ClientError as e:
        print(e)