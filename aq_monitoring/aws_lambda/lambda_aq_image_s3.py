import json, boto3
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    # print(event)
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    obj = event["Records"][0]["s3"]["object"]["key"]
    device_id, fn = obj.split("_")
    rekognition = boto3.client('rekognition')
    labels = dict()
    # Rekognition
    response = rekognition.detect_labels(
        Image={
            "S3Object":{
                "Bucket" : bucket,
                "Name" : obj
            }
        },
        MaxLabels=5,
        MinConfidence=90
    )
    # Retrieve labels
    for label in response["Labels"]:
        labels[label["Name"]] = Decimal(label["Confidence"])
    # Save to dynamodb
    # Cannot use pynamodb because it requires aws_access_id & aws_access_token which are available in ~/.aws/credentials
    # Not available in Lambda environment -> Using dynamodb will result in permission error
    db = boto3.resource("dynamodb")
    table = db.Table("AQImage")
    input = {
        "device_id" : device_id,
        "timestamp" : datetime.utcnow().isoformat(),
        "fn" : fn,
        "labels" : labels
    }
    table.put_item(Item=input)

# Create a Python AWS lambda deployment package
    # python3 -m venv env
    # source env/bin/activate
    # pip install boto3 pynamodb
    # cd env/lib/python3.6/site-packages
    # zip -r9 ${OLDPWD}/function.zip .
    # cd ${OLDPWD}
    # zip -g function.zip aq_image_lambda.py

    # Upload function.zip to the lambda function (Function code -> Code entry type -> upload a .zip file)
    # Change "Handler" to <filename.py>.<handler_method>. E.g. aq_image_lambda.lambda_handler

# Create a new role for the lambda function (https://aws.amazon.com/blogs/security/how-to-create-an-aws-iam-policy-to-grant-aws-lambda-access-to-an-amazon-dynamodb-table/)
    # Attach policies to the new role created
    # Permissions required by the lambda function:
        # AWSLambdaBasicExecution
        # AmazonRekognitionReadOnlyAccess
        # AWSLambdaExecute -> To read S3 images and pass to recoknigtion
        # DynamoDB PutItem permission
        # lambda:InvokeFunction (will be auto added when configued S3 to invoke Lambda function below)

# Create Lambda function with the new role
    # Copy in the code
    # Test with the sample event passed from S3 provided below

# Configure S3 to invoke the Lambda function when file upload (https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html#with-s3-example-configure-event-source)
    # Open the Amazon S3 console.
    # Choose the source bucket.
    # Choose Properties.
    # Under Events, configure a notification with the following settings.
    # Name – lambda-trigger.
    # Events – ObjectCreate (All).
    # Send to – Lambda function.
    # Lambda – <new lambda function>

# Sample Event
#     {
#   "Records": [
#     {
#       "eventVersion": "2.0",
#       "eventSource": "aws:s3",
#       "awsRegion": "us-west-2",
#       "eventTime": "1970-01-01T00:00:00.000Z",
#       "eventName": "ObjectCreated:Put",
#       "userIdentity": {
#         "principalId": "AIDAJDPLRKLG7UEXAMPLE"
#       },
#       "requestParameters": {
#         "sourceIPAddress": "127.0.0.1"
#       },
#       "responseElements": {
#         "x-amz-request-id": "C3D13FE58DE4C810",
#         "x-amz-id-2": "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD"
#       },
#       "s3": {
#         "s3SchemaVersion": "1.0",
#         "configurationId": "testConfigRule",
#         "bucket": {
#           "name": "aq-s3-bucket",
#           "ownerIdentity": {
#             "principalId": "A3NL1KOZZKExample"
#           },
#           "arn": "arn:aws:s3:::sourcebucket"
#         },
#         "object": {
#           "key": "woodlands_d3e834a52bdf0354.jpg",
#           "size": 1024,
#           "eTag": "d41d8cd98f00b204e9800998ecf8427e",
#           "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko"
#         }
#       }
#     }
#   ]
# }