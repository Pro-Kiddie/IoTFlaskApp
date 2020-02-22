from models import AQImage, AirQuality, Status, Device, User
import boto3, botocore, json, bcrypt, pynamodb

# Setup AWS - Needs to have .credentials setup
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
    
    if not User.exists():
        User.create_table(read_capacity_units=rcu, write_capacity_units=wcu, wait=True)
        print("User table created.")

    # Create web app default admin account if does not exists
    try:
        password_hash = bcrypt.hashpw(config["admin_password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        admin = User(config["admin_email"], name=config["admin_name"], password=password_hash)
        admin.save(~User.email.exists())
    except pynamodb.exceptions.PutError:
        print("The web app admin account already exists.")

    # Tries to create the s3 bucket if it does not exists
    try:
        s3 = boto3.resource("s3")
        bucket = config.get("aws_s3_bucket")
        s3.meta.client.head_bucket(Bucket=bucket) # Check if bucket exists
    except botocore.exceptions.ClientError as e:
        # Create bucket
        s3.create_bucket(Bucket=bucket) # By default, the bucket is created in the US East (N. Virginia) Region
        s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={ # Block public access to s3 bucket
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
            }
        )
        print("The S3 bucket to store AQ images have been created.")
    else:
        print("The '{}' already exists.".format(bucket))
