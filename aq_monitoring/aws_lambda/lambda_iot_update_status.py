import json, boto3

def lambda_handler(event, context):
    # Retrieve partition key and status from payload
    device_comp = event["device_comp"]
    status = event["status"]
    # Access Table
    db = boto3.resource("dynamodb")
    status_table = db.Table("Status")
    # Update item (entries of different components of devices should already be created)
    status_table.update_item(
        Key={
            'device_comp': device_comp,
        },
        UpdateExpression="set #ns = :s",
        ExpressionAttributeValues={
            ':s': status
        },
        ExpressionAttributeNames={
            "#ns": "status"
        }
    )
    
# Sample MQTT payload
# {
#     "device_comp" : "woodlands_led",
#     "status" : "on"
    
# }