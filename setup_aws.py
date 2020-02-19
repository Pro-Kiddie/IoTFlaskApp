from aq_monitoring.models import AQImage, AirQuality, Status, Device
import boto3, botocore, json

# Setup AWS
with open("config.json", "r") as config_file:
    config = json.load(config_file)

    rcu = 1
    wcu = 1
    # Create all the tables 
    if not AirQuality.exists():
        AirQuality.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("AirQuality table created.")

    if not Status.exists():
        Status.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("Status table created.")

    if not Device.exists():
        Device.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("Device table created.")

    if not AQImage.exists():
        AQImage.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("AQImage table created.")

    # items = AirQuality.query("woodlands", scan_index_forward=False, limit=1)
    # last_rec = items.next()
    # earliest_time = last_rec.timestamp - timedelta(hours=2)
    # print(earliest_time)
    # items = AirQuality.query("woodlands", AirQuality.timestamp < earliest_time, scan_index_forward=False)
    # for item in items:
    #     print(item)

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
