import json, boto3, secrets, base64
from io import BytesIO

# Require AWSLambdaExecute policy in its role to put item in S3
def lambda_handler(event, context):
    device_id = event["device_id"]
    pic_stream = BytesIO(base64.decodebytes(event["image"].encode("utf-8")))
    pic_stream.seek(0)
    
    s3 = boto3.client("s3")
    s3_fn = device_id + "_" + secrets.token_hex(8) + ".jpg"
    s3.upload_fileobj(pic_stream, "aq-s3-bucket", s3_fn)

# Get the topic that triggers the lambda using a query string in the AWS IoT Rule Engine like:
# SELECT *, topic(3) AS device_id from "aq/image/+"
# payload will contain 
# event = {
#           "image": base64_encoded_string,
#           "device_id" : device_id
#         }

# topic() = "aq/image/<device_id>"
# topic(1) = "aq"  
# https://docs.aws.amazon.com/iot/latest/developerguide/iot-sql-functions.html#iot-function-topic