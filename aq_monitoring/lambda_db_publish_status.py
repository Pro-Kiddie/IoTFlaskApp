import json, boto3

# Permissions needed: "iot:Publish", 
                # dynamodb:DescribeStream",
                # "dynamodb:GetRecords",
                # "dynamodb:GetShardIterator",
                # "dynamodb:ListStreams"
def lambda_handler(event, context):
    try:
        # Iterate over all the changes in Status table
        for record in event["Records"]:
            # If the change is an update operation, an IoT device's component status changed
            # Change can be caused by web client, the device itself, or telegram
            if record["eventName"] == "MODIFY":
                device_comp = record["dynamodb"]["Keys"]["device_comp"]["S"]
                device_id, comp = device_comp.split("_")
                new_status = record["dynamodb"]["NewImage"]["status"]["S"]

                # Publish the change to the relevant IoT devices
                client = boto3.client("iot-data", region_name="us-east-1")
                response = client.publish(
                    topic="status/{}/{}".format(device_id, comp),
                    qos=1,
                    payload=json.dumps({"comp" : comp, "status" : new_status})
                )
    except Exception as e:
        print(e)
        
# https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html
# {
#   "Records": [
#           {
#       "eventID": "2",
#       "eventVersion": "1.0",
#       "dynamodb": {
#         "OldImage": {
#           "Message": {
#             "S": "New item!"
#           },
#           "Id": {
#             "N": "101"
#           }
#         },
#         "SequenceNumber": "222",
#         "Keys": {
#           "device_comp": {
#             "S": "woodlands_pm25Threshold"
#           }
#         },
#         "SizeBytes": 59,
#         "NewImage": {
#           "status": {
#             "S": "55"
#           }
#         },
#         "StreamViewType": "NEW_AND_OLD_IMAGES"
#       },
#       "awsRegion": "us-west-2",
#       "eventName": "MODIFY",
#       "eventSourceARN": "test",
#       "eventSource": "aws:dynamodb"
#     },
#     {
#       "eventID": "1",
#       "eventVersion": "1.0",
#       "dynamodb": {
#         "Keys": {
#           "Id": {
#             "N": "101"
#           }
#         },
#         "NewImage": {
#           "Message": {
#             "S": "New item!"
#           },
#           "Id": {
#             "N": "101"
#           }
#         },
#         "StreamViewType": "NEW_AND_OLD_IMAGES",
#         "SequenceNumber": "111",
#         "SizeBytes": 26
#       },
#       "awsRegion": "us-west-2",
#       "eventName": "INSERT",
#       "eventSourceARN": "test",
#       "eventSource": "aws:dynamodb"
#     }
#     ]
# }  